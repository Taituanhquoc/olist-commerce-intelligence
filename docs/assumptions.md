# Assumptions and cleaning decisions

Generated from `reports/cleaning_log.csv` and `reports/audit_checks.csv`. Every cleaning step lists its row impact.

## Scope and definitions

- **Analysis window:** orders purchased from 2017-01-01 up to 2018-08-31 inclusive. Earlier and later months are partial data-collection months.
- **Revenue:** sum of item `price`; freight is reported separately. Payments are not used for revenue because they include installment interest.
- **Order in scope:** status is not `canceled` or `unavailable`, and the order has at least one item.
- **Customer:** `customer_unique_id` (Olist issues a new `customer_id` per order).
- **Late:** delivered to the customer on a later calendar day than `order_estimated_delivery_date`.
- **Review:** the latest answered review per order.
- **RFM snapshot:** 2018-09-01. Recency and monetary scored with `NTILE(5)`; frequency scored from the order count.
- **Impact assumptions:** see the *Impact model* sheet of the Excel workbook; all inputs are also stored in `reports/facts.json` under `analysis.assumptions`.

## Cleaning log (Python layer, `src/clean.py`)

| Step | Table | Action | Rows before | Rows after | Rows affected | Why |
|---|---|---|---|---|---|---|
| 1 | orders | Drop duplicate order_id | 99,441 | 99,441 | 0 | Order grain must be unique; keep earliest. |
| 2 | orders | Keep purchases 2017-01-01 to 2018-08-31 | 99,441 | 99,092 | 349 | Months outside the window are partial (data collection start/end) and distort MoM growth. |
| 3 | orders | Exclude canceled and unavailable orders | 99,092 | 97,910 | 1,182 | These orders generated no revenue; counting them would overstate demand. |
| 4 | products | Translate two categories missing from the translation file | 32,951 | 32,951 | 13 | pc_gamer and portateis_cozinha_e_preparadores_de_alimentos mapped by hand. |
| 5 | products | Label products with no category as 'unknown' | 32,951 | 32,951 | 610 | Kept: their revenue is real; dropping them would understate totals. |
| 6 | orders | Drop orders with no order items | 97,910 | 97,905 | 5 | No items means no revenue or category; these are data gaps, not sales. |
| 7 | order_reviews | Keep the latest review per order | 99,224 | 98,673 | 551 | Some orders carry several reviews; the latest answer reflects the final experience. |
| 8 | orders | Treat 'delivered' orders with no delivery date as not delivered | 97,905 | 97,905 | 8 | Delivery time and lateness cannot be measured without the date. |
| 9 | orders | Flag (not drop) carrier pickup timestamps earlier than purchase | 97,905 | 97,905 | 166 | Timestamp noise in an unused field; customer delivery dates are consistent. |
| 10 | order_items | Keep high-price items above the 99.9th percentile | 111,752 | 111,752 | 111 | Prices up to R$6,735 are plausible (furniture, electronics); not errors. |

The SQL staging layer (`sql/01_staging_clean.sql`) applies the same rules with flags instead of deletes; `tests/test_metrics.py`
checks that both layers give the same orders, revenue, repeat rate and on-time rate.

## Data audit (raw layer, `src/audit.py`)

| Check | Count |
|---|---|
| duplicate order_id in orders | 0 |
| duplicate (order_id, order_item_id) in order_items | 0 |
| orders with more than one review | 547 |
| duplicate review_id rows | 814 |
| order_items with no matching order | 0 |
| orders with no order_items | 775 |
| orders with no payment row | 1 |
| orders whose customer_id is missing from customers | 0 |
| items whose product_id is missing from products | 0 |
| products with no category | 610 |
| categories with no English translation | 2 |
| status 'delivered' but no delivery date | 8 |
| carrier pickup recorded before purchase | 166 |
| delivery recorded before purchase | 0 |
| items with price <= 0 | 0 |
| payments with value 0 | 9 |
| geolocation points outside Brazil's bounding box | 42 |
| orders purchased outside the analysis window | 349 |

Column-level profile (nulls, distinct values, ranges, IQR outliers): `reports/audit_table.csv`.
