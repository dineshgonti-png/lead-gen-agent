#!/usr/bin/env python3
"""
Lead Generation Agent — CLI entry point.

Usage:
    # Full pipeline (all portals → company filter → stakeholder search → CSV)
    python main.py run

    # Specific portals only
    python main.py run --portals linkedin naukri

    # Custom search queries
    python main.py run --queries "React Developer" "Frontend Engineer"

    # Stakeholders only (provide company list)
    python main.py stakeholders --companies "Visa" "Swiggy" "Zomato"

    # Stakeholders from a file (one company per line)
    python main.py stakeholders --file companies.txt

    # With custom output name
    python main.py run --output my_leads.csv

    # Non-headless (visible browser for debugging)
    python main.py run --no-headless
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.orchestrator import LeadGenOrchestrator
from src.utils.logger import setup_logger

log = setup_logger("main")


def cmd_run(args):
    """Run the full pipeline."""
    orch = LeadGenOrchestrator(
        portals=args.portals,
        queries=args.queries,
        output_dir=args.output_dir,
        existing_companies_file=args.existing,
        headless=not args.no_headless,
        profile_dir=args.profile,
    )
    output = orch.run(output_filename=args.output)
    if output:
        print(f"\nOutput saved to: {output}")
    else:
        print("\nNo output generated (no new companies/contacts found).")


def cmd_stakeholders(args):
    """Search stakeholders for specific companies."""
    companies = list(args.companies or [])

    if args.file:
        with open(args.file) as f:
            for line in f:
                name = line.strip()
                if name:
                    companies.append(name)

    if not companies:
        print("Error: provide --companies or --file")
        sys.exit(1)

    print(f"Searching stakeholders for {len(companies)} companies...")

    orch = LeadGenOrchestrator(
        output_dir=args.output_dir,
        existing_companies_file=args.existing,
        headless=not args.no_headless,
        profile_dir=args.profile,
    )
    output = orch.run_stakeholders_only(companies, output_filename=args.output)
    if output:
        print(f"\nOutput saved to: {output}")
    else:
        print("\nNo output generated.")


def main():
    parser = argparse.ArgumentParser(
        description="Lead Generation Agent — Automated stakeholder finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory for CSV files (default: data/output)",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output CSV filename",
    )
    parser.add_argument(
        "--existing", default=None,
        help="Path to existing companies text file (one per line)",
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Run browser in visible mode (for debugging)",
    )
    parser.add_argument(
        "--profile", default=None,
        help="Chrome profile directory (to reuse logged-in sessions)",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # -- run --
    run_parser = sub.add_parser("run", help="Run full pipeline")
    run_parser.add_argument(
        "--portals", nargs="+",
        choices=["linkedin", "naukri", "glassdoor", "foundit", "indeed", "shine"],
        help="Job portals to search (default: all)",
    )
    run_parser.add_argument(
        "--queries", nargs="+",
        help="Job search queries (default: from config)",
    )
    run_parser.set_defaults(func=cmd_run)

    # -- stakeholders --
    st_parser = sub.add_parser("stakeholders", help="Search stakeholders for specific companies")
    st_parser.add_argument(
        "--companies", nargs="+",
        help="Company names to search",
    )
    st_parser.add_argument(
        "--file", "-f", default=None,
        help="Text file with company names (one per line)",
    )
    st_parser.set_defaults(func=cmd_stakeholders)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Propagate shared args
    if not hasattr(args, "output_dir") or args.output_dir is None:
        args.output_dir = None
    if not hasattr(args, "output"):
        args.output = None
    if not hasattr(args, "existing"):
        args.existing = None
    if not hasattr(args, "no_headless"):
        args.no_headless = False
    if not hasattr(args, "profile"):
        args.profile = None

    args.func(args)


if __name__ == "__main__":
    main()
