"""
LinkedIn Jobs scraper — searches for companies hiring specific roles.
"""
import time
from typing import List
from urllib.parse import quote_plus

from config import settings
from src.utils.browser import BrowserManager
from src.utils.logger import setup_logger
from .base import BaseScraper

log = setup_logger("scraper.linkedin_jobs")


class LinkedInJobsScraper(BaseScraper):
    portal_name = "LinkedIn Jobs"

    def __init__(self, browser: BrowserManager):
        super().__init__(browser)

    def search_companies(self, query: str, max_pages: int = 3) -> List[str]:
        """Search LinkedIn Jobs for companies hiring for the given query."""
        all_companies = []
        encoded = quote_plus(query)
        base_url = settings.LINKEDIN_JOBS_URL.format(query=encoded)

        for page in range(max_pages):
            url = base_url if page == 0 else f"{base_url}&start={page * 25}"
            log.info("[%s] Page %d: %s", self.portal_name, page + 1, query)

            self.browser.get(url)
            self.browser.scroll_page(times=3, pause=2)
            time.sleep(2)

            companies = self._extract_companies()
            if not companies:
                log.info("No more companies found on page %d", page + 1)
                break

            all_companies.extend(companies)
            self.random_delay()

        unique = list(dict.fromkeys(all_companies))  # preserve order, remove dups
        log.info("[%s] Found %d unique companies for '%s'", self.portal_name, len(unique), query)
        return unique

    def _extract_companies(self) -> List[str]:
        js = """
        (() => {
            const seen = new Set();
            const companies = [];
            // LinkedIn Jobs company selectors
            const selectors = [
                '.job-card-container__primary-description',
                '.base-search-card__subtitle',
                '.artdeco-entity-lockup__subtitle',
                'a[data-tracking-control-name*="company"]',
                '.job-card-list__entity-lockup .artdeco-entity-lockup__subtitle',
            ];
            for (const sel of selectors) {
                document.querySelectorAll(sel).forEach(el => {
                    const name = el.textContent.trim().replace(/\\s+/g, ' ');
                    if (name.length > 2 && name.length < 80 && !seen.has(name.toLowerCase())) {
                        seen.add(name.toLowerCase());
                        companies.push(name);
                    }
                });
            }
            return companies;
        })()
        """
        result = self.browser.execute_js(js)
        return result if isinstance(result, list) else []
