"""
LinkedIn People Search — finds stakeholders (HR, recruiters, hiring managers)
for a given company.
"""
import time
from typing import List, Dict
from urllib.parse import quote_plus

from config import settings
from src.utils.browser import BrowserManager
from src.utils.logger import setup_logger
from .contact_extractor import ContactExtractor

log = setup_logger("extractor.linkedin_people")


class LinkedInPeopleScraper:
    """
    For each company, searches LinkedIn People to find recruiters,
    HR managers, and talent acquisition contacts.
    """

    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.extractor = ContactExtractor(browser, settings.MAX_CONTACTS_PER_COMPANY)

    def search_company_stakeholders(self, company: str) -> List[Dict[str, str]]:
        """
        Search LinkedIn People for stakeholders at the given company.
        Returns list of {"name": str, "url": str}.
        """
        all_contacts = []
        seen_urls = set()

        # Try multiple search keyword patterns
        keyword_templates = settings.STAKEHOLDER_KEYWORDS
        for template in keyword_templates:
            query = template.format(company=company)
            encoded = quote_plus(query)
            url = settings.LINKEDIN_PEOPLE_URL.format(query=encoded)

            log.info("Searching: %s", query)
            self.browser.get(url)
            self.browser.scroll_page(times=2, pause=1.5)
            time.sleep(2)

            contacts = self.extractor.extract_from_current_page()
            for c in contacts:
                clean_url = c["url"].strip().rstrip("/").split("?")[0].lower()
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    all_contacts.append(c)

            if len(all_contacts) >= settings.MAX_CONTACTS_PER_COMPANY:
                break

            self.browser.random_delay(2, 5)

        # For large companies, also try with "India" qualifier
        if len(all_contacts) < 5:
            fallback_query = f'"{company}" India recruiter HR hiring'
            encoded = quote_plus(fallback_query)
            url = settings.LINKEDIN_PEOPLE_URL.format(query=encoded)
            log.info("Fallback search: %s", fallback_query)
            self.browser.get(url)
            self.browser.scroll_page(times=2, pause=1.5)
            time.sleep(2)

            contacts = self.extractor.extract_from_current_page()
            for c in contacts:
                clean_url = c["url"].strip().rstrip("/").split("?")[0].lower()
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    all_contacts.append(c)

        final = all_contacts[: settings.MAX_CONTACTS_PER_COMPANY]
        log.info("[%s] Found %d stakeholders", company, len(final))
        return final

    def search_multiple_companies(
        self, companies: List[str]
    ) -> List[Dict[str, str]]:
        """
        Search stakeholders for multiple companies.
        Returns flat list of {"company": str, "name": str, "url": str}.
        """
        all_results = []
        for i, company in enumerate(companies, 1):
            log.info("=== Company %d/%d: %s ===", i, len(companies), company)
            contacts = self.search_company_stakeholders(company)

            if len(contacts) < settings.MIN_CONTACTS_THRESHOLD:
                log.warning(
                    "Skipping %s — only %d contacts (min %d)",
                    company,
                    len(contacts),
                    settings.MIN_CONTACTS_THRESHOLD,
                )
                continue

            for c in contacts:
                all_results.append({
                    "company": company,
                    "name": c["name"],
                    "url": c["url"],
                })

            # Batch pause every 10 companies
            if i % 10 == 0:
                log.info("Batch pause (%d companies done)...", i)
                time.sleep(settings.BATCH_PAUSE)

        log.info("Total: %d contacts across %d companies",
                 len(all_results),
                 len(set(r["company"] for r in all_results)))
        return all_results
