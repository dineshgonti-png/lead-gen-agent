"""
Base scraper class — shared logic for all job portal scrapers.
"""
import time
import random
from abc import ABC, abstractmethod
from typing import List

from config import settings
from src.utils.browser import BrowserManager
from src.utils.logger import setup_logger

log = setup_logger("scraper.base")


class BaseScraper(ABC):
    """Abstract base for all job-portal scrapers."""

    portal_name: str = "unknown"

    def __init__(self, browser: BrowserManager):
        self.browser = browser

    @abstractmethod
    def search_companies(self, query: str, max_pages: int = 3) -> List[str]:
        """Search the portal for companies hiring for the given query.
        Returns a list of company names.
        """

    def extract_companies_from_page(self) -> List[str]:
        """Default JS-based company extraction from current page."""
        js = """
        (() => {
            const seen = new Set();
            const companies = [];
            // Generic: look for company name patterns in job cards
            const els = document.querySelectorAll(
                '[class*="company"], [class*="employer"], [data-company], .companyName, .comp-name'
            );
            els.forEach(el => {
                const name = el.textContent.trim().replace(/\\s+/g, ' ');
                if (name.length > 2 && name.length < 80 && !seen.has(name.toLowerCase())) {
                    seen.add(name.toLowerCase());
                    companies.push(name);
                }
            });
            return companies;
        })()
        """
        result = self.browser.execute_js(js)
        return result if isinstance(result, list) else []

    def random_delay(self, min_s: float = None, max_s: float = None):
        mn = min_s or settings.REQUEST_DELAY_MIN
        mx = max_s or settings.REQUEST_DELAY_MAX
        time.sleep(random.uniform(mn, mx))
