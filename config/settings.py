"""
Configuration settings for the Lead Generation Agent.
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
CACHE_DIR = DATA_DIR / "cache"

# ── Selenium / Browser ────────────────────────────────────────────
CHROME_BINARY = os.getenv("CHROME_BINARY", None)  # auto-detect if None
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", None)
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))

# ── LinkedIn ──────────────────────────────────────────────────────
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

LINKEDIN_JOBS_URL = (
    "https://www.linkedin.com/jobs/search/"
    "?keywords={query}&location=India&f_TPR=r604800&sortBy=DD"
)
LINKEDIN_PEOPLE_URL = (
    "https://www.linkedin.com/search/results/people/"
    "?keywords={query}&origin=GLOBAL_SEARCH_HEADER"
)

# ── Naukri ────────────────────────────────────────────────────────
NAUKRI_SEARCH_URL = (
    "https://www.naukri.com/{slug}-jobs"
    "?k={query}&experience=0&jobAge=7"
)

# ── Glassdoor ─────────────────────────────────────────────────────
GLASSDOOR_SEARCH_URL = (
    "https://www.glassdoor.co.in/Job/india-{query}-jobs-SRCH_IL.0,5_IN115.htm"
    "?fromAge=7&sortBy=date_desc"
)

# ── Indeed / Foundit ──────────────────────────────────────────────
FOUNDIT_SEARCH_URL = (
    "https://www.foundit.in/srp/results"
    "?query={query}&locations=India&experienceRanges=0~3&sortBy=Recency"
)
INDEED_SEARCH_URL = (
    "https://in.indeed.com/jobs?q={query}&l=India&fromage=7&sort=date"
)

# ── Shine ─────────────────────────────────────────────────────────
SHINE_SEARCH_URL = (
    "https://www.shine.com/job-search/{slug}-jobs?q={query}&sort=latest"
)

# ── Search Queries ────────────────────────────────────────────────
DEFAULT_JOB_QUERIES = [
    "React Developer",
    "Frontend Developer",
    "React.js Developer",
    "Frontend Engineer",
    "UI Developer React",
    "JavaScript Developer React",
]

# ── Stakeholder Search Keywords ───────────────────────────────────
STAKEHOLDER_KEYWORDS = [
    "{company} India hiring recruiter",
    "{company} India talent acquisition",
    "{company} India HR manager",
]

# ── Filtering ─────────────────────────────────────────────────────
SKIP_COMPANIES = [
    "gamyam", "staffing", "recruitment", "talent solution",
    "people prime", "applicantz", "hackajob", "goodspace",
    "nityo infotech", "outsourced", "uplers", "scoutit",
    "consultancy", "consulting services", "manpower",
]

# ── Rate Limiting ─────────────────────────────────────────────────
REQUEST_DELAY_MIN = float(os.getenv("REQUEST_DELAY_MIN", "3"))
REQUEST_DELAY_MAX = float(os.getenv("REQUEST_DELAY_MAX", "7"))
BATCH_PAUSE = float(os.getenv("BATCH_PAUSE", "30"))
MAX_CONTACTS_PER_COMPANY = int(os.getenv("MAX_CONTACTS_PER_COMPANY", "10"))
MIN_CONTACTS_THRESHOLD = int(os.getenv("MIN_CONTACTS_THRESHOLD", "3"))

# ── Output ────────────────────────────────────────────────────────
OUTPUT_CSV_NAME = os.getenv("OUTPUT_CSV_NAME", "stakeholders_{timestamp}.csv")
CSV_HEADERS = ["Company", "Contact Name", "LinkedIn URL"]
