"""Paths and analysis constants shared by every pipeline step."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "warehouse.duckdb"
SQL_DIR = ROOT / "sql"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
SQL_OUT = REPORTS / "sql_outputs"
FACTS = REPORTS / "facts.json"
TEMPLATES = ROOT / "templates"
DOCS = ROOT / "docs"
EXCEL_PATH = ROOT / "excel" / "olist_ecommerce_kpis.xlsx"
DASHBOARD = ROOT / "dashboard" / "index.html"

# Analysis window: the 20 complete months with meaningful volume (end is exclusive).
WINDOW_START = "2017-01-01"
WINDOW_END = "2018-09-01"
SNAPSHOT_DATE = "2018-09-01"   # RFM recency is measured to this date
EXCLUDED_STATUSES = ("canceled", "unavailable")

GITHUB_USER = "TobyTY"
REPO_NAME = "ecommerce-analytics-olist"
PAGES_URL = f"https://{GITHUB_USER.lower()}.github.io/{REPO_NAME}/"
REPO_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}"

for p in (DATA_RAW, DATA_PROCESSED, FIGURES, SQL_OUT):
    p.mkdir(parents=True, exist_ok=True)
