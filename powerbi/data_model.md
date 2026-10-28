# Power BI data model

A star schema with two fact tables at different grains, both exported from `data/warehouse.duckdb`.

## Export the tables

Run once after `make all`:

```bash
python -m src.powerbi_export     # writes powerbi/export/*.csv
```

## Tables

| Table | Grain | Key columns | Use |
|---|---|---|---|
| `fact_order_items` | one row per order item | `order_id`, `product_id`, `seller_id`, `date_key`, `customer_unique_id` | Revenue, category and seller analysis |
| `fact_orders` | one row per order | `order_id`, `customer_unique_id`, `purchase_date` | Orders, AOV, delivery, reviews, payments |
| `dim_date` | one row per day, 2016-09 to 2018-10 | `date_key` | Time intelligence (mark as date table) |
| `dim_customer` | one row per `customer_unique_id` | `customer_unique_id` | Customer state, city |
| `dim_product` | one row per product | `product_id` | English category |
| `dim_seller` | one row per seller | `seller_id` | Seller state |

## Relationships (all single direction, many-to-one)

| From (many) | To (one) |
|---|---|
| `fact_order_items[date_key]` | `dim_date[date_key]` |
| `fact_order_items[product_id]` | `dim_product[product_id]` |
| `fact_order_items[seller_id]` | `dim_seller[seller_id]` |
| `fact_order_items[customer_unique_id]` | `dim_customer[customer_unique_id]` |
| `fact_orders[purchase_date]` | `dim_date[date_key]` |
| `fact_orders[customer_unique_id]` | `dim_customer[customer_unique_id]` |

`fact_orders` has no product key (an order can hold several categories). For category slicing of order-level measures, use
`fact_orders[primary_category]` (category of the highest-priced item) or keep the category slicer on item-level visuals.

## Notes

- Mark `dim_date` as the date table (Table tools > Mark as date table > `date_key`).
- Hide foreign keys in the fact tables from report view.
- Put all measures in an empty `_Measures` table (see `measures.dax`).
