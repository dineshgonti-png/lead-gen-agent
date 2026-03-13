"""
Deduplication engine for contacts and companies.
"""
import csv
from pathlib import Path
from typing import List, Set, Dict

from .logger import setup_logger

log = setup_logger("dedup")


class Deduplicator:
    """Handles URL-level and company-level deduplication across all output CSVs."""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else None
        self.seen_urls: Set[str] = set()
        self.seen_companies: Set[str] = set()

    @staticmethod
    def clean_url(url: str) -> str:
        """Normalize a LinkedIn URL for comparison."""
        return url.strip().split("?")[0].rstrip("/").lower()

    def load_existing_csvs(self, csv_paths: List[str] = None):
        """Load all existing output CSVs to build dedup sets."""
        paths = csv_paths or []

        # Auto-discover CSVs in output dir
        if self.output_dir and self.output_dir.exists():
            for f in self.output_dir.glob("*.csv"):
                if str(f) not in paths:
                    paths.append(str(f))

        for path in paths:
            p = Path(path)
            if not p.exists():
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # skip header
                    for row in reader:
                        if len(row) >= 1:
                            self.seen_companies.add(row[0].strip().lower())
                        if len(row) >= 3:
                            self.seen_urls.add(self.clean_url(row[2]))
                log.info("Loaded %s", p.name)
            except Exception as e:
                log.warning("Error loading %s: %s", path, str(e)[:80])

        log.info(
            "Dedup state: %d URLs, %d companies loaded",
            len(self.seen_urls),
            len(self.seen_companies),
        )

    def is_duplicate_url(self, url: str) -> bool:
        return self.clean_url(url) in self.seen_urls

    def is_duplicate_company(self, company: str) -> bool:
        cl = company.strip().lower()
        if cl in self.seen_companies:
            return True
        # Partial match both directions (for strings > 4 chars)
        if len(cl) > 4:
            for ex in self.seen_companies:
                if len(ex) > 4 and (cl in ex or ex in cl):
                    return True
        return False

    def add_url(self, url: str):
        self.seen_urls.add(self.clean_url(url))

    def add_company(self, company: str):
        self.seen_companies.add(company.strip().lower())

    def deduplicate_contacts(
        self, contacts: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Filter a list of contacts, removing duplicates.
        Each contact: {"company": str, "name": str, "url": str}
        """
        unique = []
        for c in contacts:
            url = c.get("url", "")
            if not url or "/in/" not in url:
                continue
            if "/edit/" in url:
                continue
            clean = self.clean_url(url)
            if clean in self.seen_urls:
                continue
            self.seen_urls.add(clean)
            unique.append(c)
        removed = len(contacts) - len(unique)
        if removed:
            log.info("Removed %d duplicate contacts", removed)
        return unique
