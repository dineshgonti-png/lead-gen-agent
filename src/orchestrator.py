"""
Main orchestrator — ties together all scrapers, extractors, and utilities
to run the full lead generation pipeline.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import settings
from src.utils.browser import BrowserManager
from src.utils.company_filter import CompanyFilter
from src.utils.dedup import Deduplicator
from src.utils.csv_writer import CSVWriter
from src.utils.logger import setup_logger

from src.scrapers.linkedin_jobs import LinkedInJobsScraper
from src.scrapers.naukri import NaukriScraper
from src.scrapers.glassdoor import GlassdoorScraper
from src.scrapers.foundit import FounditScraper
from src.scrapers.indeed import IndeedScraper
from src.scrapers.shine import ShineScraper

from src.extractors.linkedin_people import LinkedInPeopleScraper

log = setup_logger("orchestrator")


class LeadGenOrchestrator:
    """
    Full pipeline:
    1. Search job portals for companies hiring React/Frontend devs
    2. Filter new companies (skip staffing, duplicates, own company)
    3. Search LinkedIn People for stakeholders at each company
    4. Deduplicate contacts against all previous outputs
    5. Write final CSV
    """

    PORTAL_MAP = {
        "linkedin": LinkedInJobsScraper,
        "naukri": NaukriScraper,
        "glassdoor": GlassdoorScraper,
        "foundit": FounditScraper,
        "indeed": IndeedScraper,
        "shine": ShineScraper,
    }

    def __init__(
        self,
        portals: List[str] = None,
        queries: List[str] = None,
        output_dir: str = None,
        existing_companies_file: str = None,
        headless: bool = True,
        profile_dir: str = None,
    ):
        self.portal_names = portals or list(self.PORTAL_MAP.keys())
        self.queries = queries or settings.DEFAULT_JOB_QUERIES
        self.output_dir = output_dir or str(settings.OUTPUT_DIR)

        self.browser = BrowserManager(headless=headless, profile_dir=profile_dir)
        self.dedup = Deduplicator(self.output_dir)
        self.company_filter = CompanyFilter()
        self.csv_writer = CSVWriter(self.output_dir)

        if existing_companies_file:
            self.company_filter.load_existing_from_file(existing_companies_file)

        # Cache dir for intermediate JSON batches
        self.cache_dir = Path(settings.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def run(self, output_filename: str = None) -> str:
        """Run the full pipeline. Returns path to output CSV."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log.info("=" * 60)
        log.info("Lead Generation Pipeline started at %s", ts)
        log.info("Portals: %s", ", ".join(self.portal_names))
        log.info("Queries: %s", ", ".join(self.queries))
        log.info("=" * 60)

        try:
            self.browser.start()

            # Step 1: Load existing data for deduplication
            log.info("Step 1: Loading existing data for deduplication...")
            self.dedup.load_existing_csvs()
            self.company_filter.existing = self.dedup.seen_companies.copy()

            # Step 2: Login to LinkedIn
            log.info("Step 2: Logging into LinkedIn...")
            login_ok = self.browser.login_linkedin()
            if not login_ok:
                log.warning("LinkedIn login failed — results may be limited")

            # Step 3: Search job portals for hiring companies
            log.info("Step 3: Searching job portals for hiring companies...")
            raw_companies = self._search_all_portals()
            log.info("Raw companies found: %d", len(raw_companies))

            # Step 4: Filter companies
            log.info("Step 4: Filtering companies...")
            new_companies = self.company_filter.filter_companies(raw_companies)
            log.info("New unique companies: %d", len(new_companies))

            if not new_companies:
                log.info("No new companies found. Exiting.")
                return ""

            # Save company list for reference
            companies_file = self.cache_dir / f"companies_{ts}.txt"
            with open(companies_file, "w") as f:
                for c in new_companies:
                    f.write(c + "\n")

            # Step 5: Search LinkedIn for stakeholders
            log.info("Step 5: Searching LinkedIn for stakeholders...")
            people_scraper = LinkedInPeopleScraper(self.browser)
            raw_contacts = people_scraper.search_multiple_companies(new_companies)

            # Save intermediate JSON batch
            batch_file = self.cache_dir / f"batch_{ts}.json"
            self._save_batch_json(raw_contacts, str(batch_file))

            # Step 6: Deduplicate
            log.info("Step 6: Deduplicating contacts...")
            unique_contacts = self.dedup.deduplicate_contacts(raw_contacts)

            if not unique_contacts:
                log.info("All contacts were duplicates. No output generated.")
                return ""

            # Step 7: Write CSV
            log.info("Step 7: Writing output CSV...")
            fname = output_filename or f"stakeholders_{ts}.csv"
            output_path = self.csv_writer.write(unique_contacts, fname)

            # Summary
            companies_in_output = sorted(set(c["company"] for c in unique_contacts))
            log.info("=" * 60)
            log.info("PIPELINE COMPLETE")
            log.info("Companies: %d", len(companies_in_output))
            log.info("Contacts: %d", len(unique_contacts))
            log.info("Output: %s", output_path)
            log.info("=" * 60)

            return output_path

        except Exception as e:
            log.error("Pipeline error: %s", str(e), exc_info=True)
            raise
        finally:
            self.browser.quit()

    def _search_all_portals(self) -> List[str]:
        """Search all configured portals and aggregate company names."""
        all_companies = []

        for portal_name in self.portal_names:
            scraper_cls = self.PORTAL_MAP.get(portal_name)
            if not scraper_cls:
                log.warning("Unknown portal: %s", portal_name)
                continue

            scraper = scraper_cls(self.browser)
            for query in self.queries:
                try:
                    companies = scraper.search_companies(query)
                    all_companies.extend(companies)
                    log.info("[%s] '%s' → %d companies", portal_name, query, len(companies))
                except Exception as e:
                    log.error("[%s] Error searching '%s': %s", portal_name, query, str(e)[:100])

        # Deduplicate company names (case-insensitive, preserve first occurrence)
        seen = set()
        unique = []
        for c in all_companies:
            cl = c.strip().lower()
            if cl not in seen:
                seen.add(cl)
                unique.append(c.strip())

        return unique

    def _save_batch_json(self, contacts: List[dict], filepath: str):
        """Save contacts grouped by company as JSON for recovery."""
        grouped = {}
        for c in contacts:
            company = c["company"]
            if company not in grouped:
                grouped[company] = []
            grouped[company].append({"n": c["name"], "u": c["url"]})

        data = [
            {"c": company, "n": len(contacts), "r": contacts}
            for company, contacts in grouped.items()
        ]

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        log.info("Batch saved: %s (%d companies)", filepath, len(data))

    def run_stakeholders_only(
        self,
        companies: List[str],
        output_filename: str = None,
    ) -> str:
        """
        Skip portal scraping — just search stakeholders for a given list of companies.
        Useful for re-running with a manually curated company list.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            self.browser.start()
            self.dedup.load_existing_csvs()
            self.browser.login_linkedin()

            people_scraper = LinkedInPeopleScraper(self.browser)
            raw_contacts = people_scraper.search_multiple_companies(companies)

            batch_file = self.cache_dir / f"batch_{ts}.json"
            self._save_batch_json(raw_contacts, str(batch_file))

            unique_contacts = self.dedup.deduplicate_contacts(raw_contacts)
            if not unique_contacts:
                return ""

            fname = output_filename or f"stakeholders_{ts}.csv"
            return self.csv_writer.write(unique_contacts, fname)
        finally:
            self.browser.quit()
