# Provenance, attribution & responsible reuse

This project is **a documented extension of existing open-source work**, not a from-scratch implementation. This distinction matters for a credible job application.

## Upstream base (retained)

- Source repository: https://github.com/TobyTY/ecommerce-analytics-olist
- ZIP supplied by the portfolio owner: `ecommerce-analytics-olist-main.zip`.
- Upstream `LICENSE`: MIT, copyright (c) 2026 Kushal Tandon. Retained verbatim.
- Original SQL (`sql/00_*` through `sql/03_*`), Python pipeline modules (except new PromiseLab modules), executed notebooks `01`–`04`, source results, reports, Excel workbook, Power BI guidance and original Plotly dashboard are retained from the upstream project.
- The upstream report generator and one dashboard-output test were adjusted so rebuilding does not replace the portfolio homepage. The upstream README is preserved for reference at `docs/source_project_README.md`; its GitHub Pages URL refers to the **upstream**, not the present portfolio owner's deployment.
- Data source: Olist Brazilian E-Commerce public dataset (the upstream project describes its dataset licence as CC BY-NC-SA 4.0); no raw individual-level datasets are redistributed here. Check original terms before further redistribution or commercial use.

## New portfolio extension, prepared for Nguyễn Quốc Anh

A substantial new and separate decision-support feature was implemented with AI assistance, using the published aggregate results in the supplied upstream ZIP:

- `src/promise_lab.py`: data QA, Wilson 95% intervals, smoothed state risk, budget- and capacity-constrained intervention modeling, sensitivity analysis.
- `src/promise_lab_dashboard.py`, `promise_lab/index.html`, `docs/promise_lab.html`, `docs/index.html`: independent self-contained, responsive interactive delivery-promise dashboard with client-side scenario controls.
- `sql/04_delivery_promise_lab.sql`: complementary reproducible DuckDB analytics at regional and monthly grains.
- `notebooks/05_delivery_promise_lab.ipynb`, `tools/build_promise_lab_notebook.py`: an executed exploratory and decision-modeling walkthrough.
- `tests/test_promise_lab.py`, `.github/workflows/portfolio-tests.yml`: automated offline tests for the new functionality.
- `reports/promise_lab/*`, `docs/portfolio/*`, `powerbi/promise_lab_measures.dax`, README and new charts: portfolio documentation and supplementary outputs.

**Portfolio-owner responsibility:** Review, understand, rerun and personalize the methodology and reporting before claiming the work in interviews. Credit the original author/repository in your public fork or derivative. Do not describe upstream source code as solely authored by the portfolio owner. AI-assisted work should be represented in accordance with any relevant academic or employer rules.

## Claims and limitations

Observed: historical order and late-delivery counts, customer review-score associations.
Assumed: per-order intervention cost, efficacy, coverage, and business value of a late delivery avoided. A modeled value is not verified revenue, cost savings, or causal impact.

Data is from 2017–2018 and must not be represented as current market or operational performance.
