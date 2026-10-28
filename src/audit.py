"""Data audit of the raw layer: nulls, dtypes, duplicates, key integrity, date ranges, outliers.

Writes reports/audit_table.csv (one row per column) and reports/audit_checks.csv
(one row per integrity check), both read by notebooks/01_audit.ipynb.
"""
from __future__ import annotations

import pandas as pd

from src.config import REPORTS
from src.warehouse import connect

TABLES = ["orders", "order_items", "order_payments", "order_reviews", "customers",
          "products", "sellers", "geolocation", "category_translation"]

CHECKS = {
    "duplicate order_id in orders":
        "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM raw.orders",
    "duplicate (order_id, order_item_id) in order_items":
        "SELECT COUNT(*) - COUNT(DISTINCT order_id || '-' || order_item_id) FROM raw.order_items",
    "orders with more than one review":
        "SELECT COUNT(*) FROM (SELECT order_id FROM raw.order_reviews GROUP BY 1 HAVING COUNT(*) > 1)",
    "duplicate review_id rows":
        "SELECT COUNT(*) - COUNT(DISTINCT review_id) FROM raw.order_reviews",
    "order_items with no matching order":
        "SELECT COUNT(*) FROM raw.order_items i LEFT JOIN raw.orders o USING (order_id) WHERE o.order_id IS NULL",
    "orders with no order_items":
        "SELECT COUNT(*) FROM raw.orders o WHERE NOT EXISTS (SELECT 1 FROM raw.order_items i WHERE i.order_id = o.order_id)",
    "orders with no payment row":
        "SELECT COUNT(*) FROM raw.orders o WHERE NOT EXISTS (SELECT 1 FROM raw.order_payments p WHERE p.order_id = o.order_id)",
    "orders whose customer_id is missing from customers":
        "SELECT COUNT(*) FROM raw.orders o LEFT JOIN raw.customers c USING (customer_id) WHERE c.customer_id IS NULL",
    "items whose product_id is missing from products":
        "SELECT COUNT(*) FROM raw.order_items i LEFT JOIN raw.products p USING (product_id) WHERE p.product_id IS NULL",
    "products with no category":
        "SELECT COUNT(*) FROM raw.products WHERE product_category_name IS NULL",
    "categories with no English translation":
        "SELECT COUNT(DISTINCT product_category_name) FROM raw.products WHERE product_category_name NOT IN (SELECT product_category_name FROM raw.category_translation)",
    "status 'delivered' but no delivery date":
        "SELECT COUNT(*) FROM raw.orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL",
    "carrier pickup recorded before purchase":
        "SELECT COUNT(*) FROM raw.orders WHERE order_delivered_carrier_date < order_purchase_timestamp",
    "delivery recorded before purchase":
        "SELECT COUNT(*) FROM raw.orders WHERE order_delivered_customer_date < order_purchase_timestamp",
    "items with price <= 0":
        "SELECT COUNT(*) FROM raw.order_items WHERE price <= 0",
    "payments with value 0":
        "SELECT COUNT(*) FROM raw.order_payments WHERE payment_value = 0",
    "geolocation points outside Brazil's bounding box":
        "SELECT COUNT(*) FROM raw.geolocation WHERE NOT (geolocation_lat BETWEEN -33.75 AND 5.27 AND geolocation_lng BETWEEN -73.99 AND -34.79)",
    "orders purchased outside the analysis window":
        "SELECT COUNT(*) FROM raw.orders WHERE order_purchase_timestamp < TIMESTAMP '2017-01-01' OR order_purchase_timestamp >= TIMESTAMP '2018-09-01'",
}


def column_profile(con, table: str) -> pd.DataFrame:
    df = con.execute(f"SELECT * FROM raw.{table}").df()
    rows = []
    for col in df.columns:
        s = df[col]
        row = {"table": table, "column": col, "dtype": str(s.dtype), "rows": len(s),
               "nulls": int(s.isna().sum()), "null_pct": round(100 * s.isna().mean(), 2),
               "distinct": int(s.nunique(dropna=True)), "min": None, "max": None, "iqr_outliers": None}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            q1, q3 = s.quantile([0.25, 0.75])
            iqr = q3 - q1
            row.update(min=s.min(), max=s.max(),
                       iqr_outliers=int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()))
        elif pd.api.types.is_datetime64_any_dtype(s):
            row.update(min=str(s.min()), max=str(s.max()))
        rows.append(row)
    return pd.DataFrame(rows).astype({"min": object, "max": object, "iqr_outliers": object})


def run() -> tuple[pd.DataFrame, pd.DataFrame]:
    with connect(read_only=True) as con:
        profile = pd.concat([column_profile(con, t) for t in TABLES], ignore_index=True)
        checks = pd.DataFrame(
            [{"check": name, "count": int(con.execute(sql).fetchone()[0])} for name, sql in CHECKS.items()])
    profile.to_csv(REPORTS / "audit_table.csv", index=False)
    checks.to_csv(REPORTS / "audit_checks.csv", index=False)
    print(f"audit: profiled {len(profile)} columns across {len(TABLES)} tables; {len(checks)} integrity checks")
    return profile, checks


if __name__ == "__main__":
    run()
