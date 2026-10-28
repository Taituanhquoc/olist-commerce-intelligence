"""Generate and execute the four notebooks so they ship with outputs.

The notebooks are thin: they call the same src/ modules as the pipeline and display the
results, so there is one implementation of every calculation.
"""
from __future__ import annotations

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from src.config import ROOT

SETUP = """import json, pandas as pd
from IPython.display import Image, display, Markdown
pd.set_option("display.max_columns", 30); pd.set_option("display.width", 160)
facts = json.load(open("reports/facts.json", encoding="utf-8"))
a = facts["analysis"]"""

NOTEBOOKS = {
    "01_audit.ipynb": [
        new_markdown_cell("# 01 Audit\nNulls, dtypes, duplicates, key integrity, date ranges and outliers in the raw Olist tables. "
                          "Source: `src/audit.py` (queries the raw schema in `data/warehouse.duckdb`)."),
        new_code_cell(SETUP + "\nfrom src import audit\nprofile, checks = audit.run()"),
        new_markdown_cell("## Integrity checks\nEach row is one SQL check against the raw layer. Non-zero counts are handled in the cleaning step."),
        new_code_cell("checks"),
        new_markdown_cell("## Column profile: columns with missing values"),
        new_code_cell("profile[profile.nulls > 0].sort_values('null_pct', ascending=False)"),
        new_markdown_cell("## Date ranges and numeric outliers"),
        new_code_cell("profile[profile['min'].notna()][['table','column','dtype','min','max','iqr_outliers']]"),
        new_markdown_cell("**Read-out.** Duplicate reviews per order, orders without items, products without a category, untranslated "
                          "categories and partial months at the start and end of the data are the issues that matter; each is resolved "
                          "in `02_cleaning` with its row impact logged."),
    ],
    "02_cleaning.ipynb": [
        new_markdown_cell("# 02 Cleaning\nThe pandas cleaning layer (`src/clean.py`) is written independently of the SQL staging layer. "
                          "This notebook re-runs it, shows every decision with its row impact, and checks it against SQL."),
        new_code_cell(SETUP + "\nfrom src import clean\norders, items, log = clean.build()\nlog"),
        new_markdown_cell("## Cross-check against the SQL star schema"),
        new_code_cell("from src.warehouse import connect\n"
                      "with connect(read_only=True) as con:\n"
                      "    sql = con.execute('SELECT COUNT(*) AS orders, SUM(revenue) AS revenue FROM fact_orders').df()\n"
                      "py = pd.DataFrame({'orders': [len(orders)], 'revenue': [orders.revenue.sum()]})\n"
                      "pd.concat({'SQL fact_orders': sql, 'Python orders_clean': py})"),
        new_code_cell("orders.head()"),
    ],
    "03_eda.ipynb": [
        new_markdown_cell("# 03 Exploratory analysis\nEach chart's title states the finding. Figures are produced by `src/eda.py`."),
        new_code_cell(SETUP + "\nfrom src import eda\nout = eda.run()\nfor fig in out['figures']:\n    display(Image(filename=f'reports/figures/{fig}'))"),
        new_code_cell("pd.read_csv('reports/sql_outputs/monthly_kpis.csv')"),
    ],
    "04_analysis.ipynb": [
        new_markdown_cell("# 04 Core analysis\nRFM, cohorts, delivery vs review (Mann-Whitney U with effect size), state logistics, payments "
                          "and the impact model. Every value printed here is also in `reports/facts.json`."),
        new_code_cell(SETUP + "\nfrom src import analysis\nf = analysis.run()"),
        new_markdown_cell("## Q3 RFM segments"),
        new_code_cell("pd.DataFrame(f['rfm']['segments']).T.sort_values('revenue', ascending=False)"),
        new_code_cell("display(Image(filename='reports/figures/07_rfm_segments.png'))"),
        new_markdown_cell("## Q4 Cohort retention"),
        new_code_cell("display(Image(filename='reports/figures/08_cohort_heatmap.png'))\npd.Series(f['cohort'])"),
        new_markdown_cell("## Q5 Late delivery vs review score\nTwo-sided Mann-Whitney U on review scores of late vs on-time delivered orders. "
                          "Rank-biserial correlation as effect size; Welch interval for the mean gap."),
        new_code_cell("pd.Series(f['delivery'])"),
        new_code_cell("display(Image(filename='reports/figures/09_delay_vs_review.png'))\npd.Series(f['retention_vs_delivery'])"),
        new_markdown_cell("## Q6 States and Q7 payments"),
        new_code_cell("pd.DataFrame(f['state']['worst5'])"),
        new_code_cell("display(Image(filename='reports/figures/10_state_late_rate.png'))\ndisplay(Image(filename='reports/figures/11_installments_aov.png'))\npd.Series(f['payment'])"),
        new_markdown_cell("## Impact model\nAssumptions are inputs; change them in `src/analysis.py` (or in the Excel *Impact model* sheet)."),
        new_code_cell("pd.Series(f['assumptions']), pd.Series(f['impact'])"),
    ],
}


def build() -> None:
    nb_dir = ROOT / "notebooks"
    nb_dir.mkdir(exist_ok=True)
    for name, cells in NOTEBOOKS.items():
        nb = new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
        NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}).execute()
        nbformat.write(nb, nb_dir / name)
        print(f"notebooks: executed {name}")


if __name__ == "__main__":
    build()
