# Lead Generation Agent

Automated pipeline that discovers companies hiring React/Frontend developers across multiple Indian job portals, then finds HR/recruiter stakeholders on LinkedIn — producing a deduplicated CSV of leads ready for outreach.

## What It Does

1. **Scans job portals** (LinkedIn Jobs, Naukri, Glassdoor, Foundit/Indeed, Shine) for companies actively hiring
2. **Filters companies** — removes staffing agencies, duplicates, and already-tracked companies
3. **Searches LinkedIn People** for each company's recruiters, HR managers, and talent acquisition contacts
4. **Extracts up to 10 contacts per company** (name + LinkedIn profile URL)
5. **Deduplicates** against all previous output CSVs (URL-level)
6. **Outputs a clean CSV** with columns: Company, Contact Name, LinkedIn URL

## Quick Start

### Local (Python)

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/lead-gen-agent.git
cd lead-gen-agent
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your LinkedIn email/password

# Run full pipeline
python main.py run

# Run specific portals
python main.py run --portals linkedin naukri

# Search stakeholders for specific companies
python main.py stakeholders --companies "Visa" "Swiggy" "Zomato"

# From a file (one company per line)
python main.py stakeholders --file companies.txt

# Visible browser (for debugging)
python main.py run --no-headless
```

### Docker

```bash
# Build
docker build -t lead-gen-agent .

# Run full pipeline
docker run --env-file .env -v $(pwd)/data:/app/data lead-gen-agent

# Run stakeholders only
docker run --env-file .env -v $(pwd)/data:/app/data lead-gen-agent \
    stakeholders --companies "Visa" "Swiggy"

# Using docker-compose
docker-compose up lead-gen-agent
```

### GitHub Actions (Scheduled)

The workflow runs automatically every Monday and Thursday at 6 AM IST. You can also trigger it manually from the Actions tab.

**Setup:**
1. Go to your repo → Settings → Secrets and variables → Actions
2. Add these repository secrets:
   - `LINKEDIN_EMAIL` — your LinkedIn email
   - `LINKEDIN_PASSWORD` — your LinkedIn password
3. The workflow will auto-commit new CSVs to `data/output/`

**Manual trigger:**
- Go to Actions → "Lead Generation Pipeline" → Run workflow
- Optionally specify portals, queries, or a companies file

## Project Structure

```
lead-gen-agent/
├── main.py                          # CLI entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   └── settings.py                  # All configuration (env vars, URLs, defaults)
├── src/
│   ├── orchestrator.py              # Main pipeline logic
│   ├── scrapers/                    # Job portal scrapers
│   │   ├── base.py                  # Abstract base scraper
│   │   ├── linkedin_jobs.py
│   │   ├── naukri.py
│   │   ├── glassdoor.py
│   │   ├── foundit.py
│   │   ├── indeed.py
│   │   └── shine.py
│   ├── extractors/                  # LinkedIn contact extraction
│   │   ├── contact_extractor.py     # Core JS extraction logic
│   │   └── linkedin_people.py       # People search + multi-keyword
│   └── utils/
│       ├── browser.py               # Selenium manager with anti-detection
│       ├── company_filter.py        # Skip staffing/dupes/own company
│       ├── dedup.py                 # URL-level deduplication engine
│       ├── csv_writer.py            # Output CSV writer
│       └── logger.py
├── data/
│   ├── output/                      # Final CSV outputs (git-tracked)
│   └── cache/                       # Intermediate JSON batches
├── .github/
│   └── workflows/
│       └── lead-gen.yml             # Scheduled + manual trigger workflow
└── tests/
```

## Configuration

All settings are in `config/settings.py` and can be overridden via environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `LINKEDIN_EMAIL` | — | LinkedIn login email |
| `LINKEDIN_PASSWORD` | — | LinkedIn login password |
| `HEADLESS` | `true` | Run browser without GUI |
| `REQUEST_DELAY_MIN` | `3` | Min seconds between requests |
| `REQUEST_DELAY_MAX` | `7` | Max seconds between requests |
| `BATCH_PAUSE` | `30` | Seconds to pause every 10 companies |
| `MAX_CONTACTS_PER_COMPANY` | `10` | Max stakeholders to extract per company |
| `MIN_CONTACTS_THRESHOLD` | `3` | Skip companies with fewer contacts |

## Adding New Portals

1. Create a new file in `src/scrapers/` extending `BaseScraper`
2. Implement `search_companies(query, max_pages)` → returns `List[str]`
3. Add the class to `src/scrapers/__init__.py`
4. Register it in `LeadGenOrchestrator.PORTAL_MAP`

## Notes

- The agent uses Selenium with anti-detection settings (custom user-agent, disabled automation flags)
- LinkedIn may require CAPTCHA solving during login — use `--profile` to reuse a logged-in Chrome profile
- Rate limiting is built in to avoid being flagged; increase delays for safer operation
- All intermediate data is saved as JSON in `data/cache/` for recovery if the pipeline is interrupted
- The deduplication engine checks against ALL CSVs in `data/output/`, so you never get duplicate contacts across runs
