"""
Company filtering — skip staffing agencies, duplicates, and own company.
"""
from typing import List, Set

from config import settings
from .logger import setup_logger

log = setup_logger("company_filter")


class CompanyFilter:
    """Filters companies against skip-list and existing tracked companies."""

    def __init__(self, skip_words: List[str] = None, existing_companies: Set[str] = None):
        self.skip_words = [w.lower() for w in (skip_words or settings.SKIP_COMPANIES)]
        self.existing = {c.lower() for c in (existing_companies or set())}

    def load_existing_from_file(self, filepath: str):
        """Load existing company names from a text file (one per line)."""
        try:
            with open(filepath) as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        self.existing.add(name)
            log.info("Loaded %d existing companies from %s", len(self.existing), filepath)
        except FileNotFoundError:
            log.warning("File not found: %s", filepath)

    def should_skip(self, company: str) -> bool:
        """Check if a company should be skipped."""
        cl = company.strip().lower()

        # Skip staffing/recruitment companies
        if any(sw in cl for sw in self.skip_words):
            log.debug("SKIP (staffing): %s", company)
            return True

        # Exact match
        if cl in self.existing:
            log.debug("SKIP (exists): %s", company)
            return True

        # Partial match both directions
        if len(cl) > 4:
            for ex in self.existing:
                if len(ex) > 4 and (cl in ex or ex in cl):
                    log.debug("SKIP (partial match '%s'): %s", ex, company)
                    return True

        return False

    def filter_companies(self, companies: List[str]) -> List[str]:
        """Return only new, non-staffing companies."""
        new = []
        for c in companies:
            if not self.should_skip(c):
                new.append(c)
                self.existing.add(c.strip().lower())  # track to avoid dups within batch
        log.info("Filtered %d → %d new companies", len(companies), len(new))
        return new
