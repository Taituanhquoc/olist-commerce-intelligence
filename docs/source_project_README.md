# E-Commerce Sales, Customer and Delivery Analytics (Olist, real data)

**Live dashboard:** https://tobyty.github.io/ecommerce-analytics-olist/ · **Data:** Olist Brazilian E-Commerce public dataset, 97,905 real orders, Jan 2017 to Aug 2018

> **Headline: growth has stalled because the business only acquires.** Jan-Aug revenue grew 138% year on year,
> but the 2018 monthly run-rate is flat (May-Aug averaged R$896k a month against
> R$939k in Jan-Apr). New customers stopped growing at about 6,459 a month,
> only 3.0% of customers ever order twice, and late deliveries cut the average review from 4.29
> to 2.27 stars. Three actions below are worth an estimated **R$275k a year**
> (2.5% of annualised 2018 revenue) under stated assumptions.

![Executive overview](reports/figures/dashboard_overview.png)

## Key numbers

| Metric | Value | Definition |
|---|---|---|
| Revenue | R$13.45M | Sum of item prices, excluding freight (R$2.23M freight on top) |
| Orders | 97,905 | Orders in the window, excluding canceled and unavailable |
| Customers | 94,703 | Distinct `customer_unique_id` |
| Average order value | R$137.37 | Revenue / orders |
| Repeat purchase rate | 3.03% | Customers with 2+ orders / all customers |
| On-time delivery | 93.2% | Delivered on or before the promised date |
| Average delivery time | 12.5 days | Purchase to customer receipt |
| Average review | 4.12 / 5 | Latest review per order |

## What holds back growth, and three actions

| # | Action | Evidence | Estimated annual impact |
|---|---|---|---|
| 1 | **Second-purchase programme** aimed at Promising and At-Risk one-time buyers (post-delivery voucher, category-matched recommendations) | 28,779 high-value one-time buyers are 30% of customers but 57% of revenue; month-1 retention is 0.48% | **R$95.1k** if repeat rate rises 1.0 pp (range R$47.5k to R$190k for 0.5 to 2.0 pp) |
| 2 | **Fix delivery promises in the 14 states above the national late rate** (carrier mix, realistic ETAs for the North-East and RJ) | These states receive 30% of deliveries but 51% of late orders; RJ alone holds 23%; late orders average 2.27 stars | **1,477 fewer late orders a year** and +0.04 on the platform review average; direct repeat revenue is small (R$945) |
| 3 | **Cross-sell to build baskets** in the top categories ("bought together" bundles at checkout) | Only 9.9% of orders have more than one item; an add-on is worth R$111.27 on average | **R$179k** if multi-item share rises 2.0 pp |

Assumptions: annual volumes use the 2018 run-rate (77,509 new customers and 80,295 orders a year);
a repeat order is worth R$122.64 (observed average). The lifts are planning assumptions, not measured effects: run each action as an A/B test
before scaling. The impact model is live in `excel/olist_ecommerce_kpis.xlsx` (sheet *Impact model*) so the assumptions can be changed.

## Answers to the seven business questions

1. **Trend.** Revenue rose from R$120k in Jan 2017 to a Black-Friday peak of R$1.00M in Nov 2017, then flattened.
   Average month-on-month growth fell from 22.7% in 2017 to 2.5% in 2018. The YoY gain is all volume
   (orders 137%, AOV 0.4%).
   ![Monthly revenue](reports/figures/01_monthly_revenue.png)
2. **Categories and sellers.** The top 10 of 74 categories carry 62% of revenue, the bottom half only
   3.7%. The top 10% of 3,029 sellers earn 67%.
   Largest category: health beauty (9.3%).
3. **RFM segments.** Champions and Loyal (the only repeat buyers) are 3.0% of customers. Promising and At-Risk
   one-time buyers are the value pool: 57% of revenue.
   ![RFM segments](reports/figures/07_rfm_segments.png)
4. **Cohorts and repeat purchase.** No cohort retains more than 0.7% in any later month;
   3.2% of customers buy again within 180 days, and repeat orders are 2.9% of revenue.
   ![Cohort heatmap](reports/figures/08_cohort_heatmap.png)
5. **Late delivery vs review.** Late orders average 2.27 stars against 4.29 on time, a gap of
   2.02 stars (95% CI 1.98 to 2.06). Mann-Whitney U: p < 0.001,
   rank-biserial effect size -0.64 (large). Orders 8+ days late average 1.70 stars and 79%
   of their reviews are 1-2 stars.
   ![Delay vs review](reports/figures/09_delay_vs_review.png)
6. **Logistics by state.** Worst late rates: AL 21.5%, MA 17.5%, SE 15.4%
   (national 6.8%). RJ combines volume with a high rate (12.1%): 1,495 late orders,
   second only to SP (1,817), whose rate is just 4.5%.
   ![State late rate](reports/figures/10_state_late_rate.png)
7. **Payment mix.** Credit card pays for 75% of orders, boleto 20%. Credit-card order value rises with
   installments, from R$82.62 (single payment) to R$301.79 (7+), Spearman
   rho 0.45. This is a correlation, not proof that installments cause bigger baskets.

More detail: [executive summary](reports/executive_summary.md) · [insights and recommendations](reports/insights_and_recommendations.md) ·
[assumptions and cleaning log](docs/assumptions.md) · [project brief](docs/project_brief.md) · [interview notes](docs/interview_talking_points.md)

## What is in the repo

| Path | Contents |
|---|---|
| `sql/` | `00_schema` (typed raw layer + indexes), `01_staging_clean` (dedup, flags), `02_analysis_views` (star schema: `fact_order_items`, `fact_orders`, `dim_customer/product/seller/date/geo`; cohort, RFM with `NTILE`, MoM/YoY with `LAG`, top-N with `ROW_NUMBER`), `03_kpi_queries` |
| `src/` | Pipeline: download, warehouse build (DuckDB), audit, cleaning, EDA, analysis, Excel, dashboard, reports |
| `notebooks/` | `01_audit`, `02_cleaning`, `03_eda`, `04_analysis`, executed with outputs |
| `excel/olist_ecommerce_kpis.xlsx` | Formula-driven KPI workbook: summary, monthly MoM/YoY, category Pareto, state logistics, RFM, payments, impact model with inputs and sensitivity |
| `dashboard/index.html` | Self-contained Plotly dashboard (works offline), also served by GitHub Pages from `docs/` |
| `powerbi/` | Data model, 16 DAX measures, theme, page layout and a click-by-click build guide (no `.pbix` is committed) |
| `reports/` | `facts.json` (every published number), executive summary, insights, figures, SQL outputs |
| `tests/` | Data-quality and metric tests: SQL, Python, Excel and dashboard totals must agree |

## Run it

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make all        # download -> warehouse -> audit -> clean -> eda -> analysis -> excel -> dashboard -> reports -> notebooks -> test -> check
```

`make all` rebuilds everything from the raw download. The data is fetched with `kagglehub` (no Kaggle login needed for this dataset) and falls
back to a public GitHub mirror. Raw files are not committed: the geolocation file alone is 61.3 MB, and the licence restricts redistribution.

## Method notes

- **Scope.** Purchases from 2017-01-01 to 2018-08-31; canceled and unavailable orders removed. The 349 orders outside the window sit in partial months at the start and end of data collection.
- **Two independent implementations.** The SQL star schema and the pandas cleaning layer are written separately; tests require identical order counts, revenue, repeat rate and on-time rate.
- **RFM.** Recency and monetary use `NTILE(5)`. Frequency uses the order count, because 97.0% of customers have exactly one order and a frequency quintile would be meaningless.
- **Late delivery.** An order is late when delivered after the promised date (day grain). Effect size is reported because with 95,560 reviewed orders any difference is "significant".
- **Every number is generated.** README, summaries and dashboard text are rendered from `reports/facts.json`; `tools/check_numbers.py` fails the build if a number cannot be traced.

## Limitations

- No cost data: the dataset has prices and freight but no product cost, so this analyses revenue, not profit.
- Late first deliveries are linked to a lower repeat rate (2.54% vs 3.06%, p = 0.019), but the gap is small: delivery is mainly a review-score problem, not the main reason customers do not return.
- Impact estimates use assumed lifts; they size the opportunity, they do not forecast it.

Data licence: CC BY-NC-SA 4.0 (Olist). Code licence: MIT.
