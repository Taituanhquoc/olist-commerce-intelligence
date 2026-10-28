"""Render README, executive summary, insights, interview notes, assumptions and data README.

Templates in templates/*.j2 read only from reports/facts.json (plus the cleaning and audit
logs, which are copied into facts.json first), so check_numbers.py can trace every number.
"""
from __future__ import annotations

import json
import re

import pandas as pd
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src import facts
from src.config import DATA_RAW, DOCS, PAGES_URL, REPO_URL, REPORTS, ROOT, TEMPLATES
from src.download import EXPECTED
from src.fmt import FILTERS

OUTPUTS = {
    "README.md.j2": DOCS / "source_project_README.md",
    "executive_summary.md.j2": REPORTS / "executive_summary.md",
    "insights_and_recommendations.md.j2": REPORTS / "insights_and_recommendations.md",
    "interview_talking_points.md.j2": DOCS / "interview_talking_points.md",
    "assumptions.md.j2": DOCS / "assumptions.md",
    "data_README.md.j2": ROOT / "data" / "README.md",
}


def count_measures() -> int:
    """Measures in powerbi/measures.dax are written as a 'Name =' line followed by the expression."""
    text = (ROOT / "powerbi" / "measures.dax").read_text(encoding="utf-8")
    return len([m for m in re.findall(r"^([A-Z][^=\n]*?)\s=\s*$", text, re.M) if not m.startswith(("VAR", "RETURN"))])


def data_quality() -> dict:
    log = pd.read_csv(REPORTS / "cleaning_log.csv")
    checks = pd.read_csv(REPORTS / "audit_checks.csv")
    raw_rows = [{"file": f, "rows": len(pd.read_csv(DATA_RAW / f, usecols=[0]))} for f in EXPECTED]
    outside = int(checks.loc[checks.check == "orders purchased outside the analysis window", "count"].iloc[0])
    items = pd.read_csv(DATA_RAW / "olist_order_items_dataset.csv", usecols=["price"])
    q = {
        "log": log.to_dict("records"), "checks": checks.to_dict("records"), "raw_rows": raw_rows,
        "outside_window": outside, "max_item_price": float(items.price.max()),
        "geolocation_mb": (DATA_RAW / "olist_geolocation_dataset.csv").stat().st_size / 1e6,
        "validation_tolerance_pct": 20, "price_outlier_percentile": 99.9,
        "dax_measures": count_measures(),
    }
    return q


def build() -> None:
    facts.update("data_quality", data_quality())
    f = facts.read()
    src = json.loads((DATA_RAW / "_source.json").read_text(encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(TEMPLATES), undefined=StrictUndefined, keep_trailing_newline=True,
                      trim_blocks=False, lstrip_blocks=False)
    env.filters.update(FILTERS)
    ctx = {"a": f["analysis"], "e": f["eda"], "q": f["data_quality"], "src": src, "pages_url": PAGES_URL,
           "repo_url": REPO_URL, "powerbi_measures": f["data_quality"]["dax_measures"],
           "log": f["data_quality"]["log"], "checks": f["data_quality"]["checks"]}
    for tpl, out in OUTPUTS.items():
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(env.get_template(tpl).render(**ctx), encoding="utf-8")
        print(f"report: wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
