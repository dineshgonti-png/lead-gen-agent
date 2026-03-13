"""
Glassdoor India scraper.
"""
import time
from typing import List
from urllib.parse import quote_plus

from config import settings
from src.utils.browser import BrowserManager
from src.utils.logger import setup_logger
from .base import BaseScraper

log = setup_logger("scraper.glassdoor")


class GlassdoorScraper(BaseScraper):
    portal_name = "Glassdoor"

    def search_companies(self, query: str, max_pages: int = 2) -> List[str]:
        all_companies = []
        slug = query.lower().replace(" ", "-")
        base_url = settings.GLASSDOOR_SEARCH_URL.format(query=slug)

        for page in range(max_pages):
            url = base_url if page == 0 else f"{base_url}&p={page + 1}"
            log.info("[%s] Page %d: %s", self.portal_name, page + 1, query)

            self.browser.get(url)
            self.browser.scroll_page(times=2, pause=1.5)
            time.sleep(2)

            companies = self._extract_companies()
            if not companies:
                break
            all_companies.extend(companies)
            self.random_delay()

        unique = list(dict.fromkeys(all_companies))
        log.info("[%s] Found %d unique companies for '%s'", self.portal_name, len(unique), query)
        return unique

    def _extract_companies(self) -> List[str]:
        js = """
        (() => {
            const seen = new Set();
            const companies = [];
            const selectors = [
                '[data-test="employer-short-name"]',
                '.css-l2wjgv', '.e1n63ojh0',
                '.jobCard .employer-name',
                'span[class*="EmployerName"]',
            ];
            for (const sel of selectors) {
                document.querySelectorAll(sel).forEach(el => {
                    let name = el.textContent.trim().replace(/\\s+/g, ' ');
                    name = name.replace(/\\d+\\.\\d+\\s*★?$/, '').trim();
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
