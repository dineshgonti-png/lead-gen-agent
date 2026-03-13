"""
CSV output writer.
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from config import settings
from .logger import setup_logger

log = setup_logger("csv_writer")


class CSVWriter:
    """Writes contact data to CSV files."""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        contacts: List[Dict[str, str]],
        filename: str = None,
    ) -> str:
        """
        Write contacts to CSV.
        contacts: list of {"company": str, "name": str, "url": str}
        Returns: path to written file.
        """
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stakeholders_{ts}.csv"

        filepath = self.output_dir / filename
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(settings.CSV_HEADERS)
            for c in contacts:
                writer.writerow([c["company"], c["name"], c["url"]])

        companies = sorted(set(c["company"] for c in contacts))
        log.info(
            "Wrote %d contacts (%d companies) → %s",
            len(contacts),
            len(companies),
            filepath.name,
        )
        return str(filepath)
