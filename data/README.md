# Data

**Real data.** Olist Brazilian E-Commerce Public Dataset.

| Field | Value |
|---|---|
| Source used | kaggle (https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) |
| Fallback | Public GitHub mirror of the original CSVs (`src/download.py`), used only if Kaggle fails validation |
| Licence | CC BY-NC-SA 4.0 (as published by Olist on Kaggle) |
| Retrieved | 2026-10-06 |
| Files | 9 CSVs, downloaded to `data/raw/` at build time (not committed) |

Validation on download: every file must exist, contain its expected columns, have a row count within 20% of the published size and
non-null key columns; otherwise the next source is tried.

## Files and row counts

| File | Rows |
|---|---|
| `olist_customers_dataset.csv` | 99,441 |
| `olist_geolocation_dataset.csv` | 1,000,163 |
| `olist_order_items_dataset.csv` | 112,650 |
| `olist_order_payments_dataset.csv` | 103,886 |
| `olist_order_reviews_dataset.csv` | 99,224 |
| `olist_orders_dataset.csv` | 99,441 |
| `olist_products_dataset.csv` | 32,951 |
| `olist_sellers_dataset.csv` | 3,095 |
| `product_category_name_translation.csv` | 71 |

## Data dictionary (fields used)

| Table | Field | Meaning |
|---|---|---|
| orders | `order_id` | Order key |
| orders | `customer_id` | Per-order customer key; maps to `customer_unique_id` |
| orders | `order_status` | delivered, shipped, canceled, unavailable, invoiced, processing, created, approved |
| orders | `order_purchase_timestamp` | Purchase time; drives month, cohort and window |
| orders | `order_delivered_customer_date` | Delivery to customer; drives delivery days and lateness |
| orders | `order_estimated_delivery_date` | Date promised to the customer at purchase |
| order_items | `order_item_id` | Item sequence within the order |
| order_items | `price`, `freight_value` | Item price and freight (BRL) |
| order_items | `seller_id`, `product_id` | Seller and product keys |
| order_payments | `payment_type`, `payment_installments`, `payment_value` | Payment method, installments, amount |
| order_reviews | `review_score`, `review_answer_timestamp` | 1-5 score and when it was answered |
| customers | `customer_unique_id`, `customer_state`, `customer_zip_code_prefix` | Person key and location |
| products | `product_category_name` | Portuguese category; translated with `product_category_name_translation` |
| sellers | `seller_state` | Seller location |
| geolocation | `geolocation_zip_code_prefix`, `lat`, `lng` | Points per zip prefix (median taken in `dim_geo`) |

## Processed outputs

- `data/warehouse.duckdb`: raw, staging and star-schema tables (rebuilt by `make warehouse`).
- `data/processed/orders_clean.parquet`, `items_clean.parquet`: Python cleaning layer.
