"""Python cleaning layer, written independently of the SQL staging layer.

Builds the order-grain analysis table from the raw CSVs with pandas, logging every
decision and its row impact to reports/cleaning_log.csv. tests/test_metrics.py then
checks that this table and the SQL fact_orders agree on counts and totals, so the two
implementations verify each other.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, DATA_RAW, EXCLUDED_STATUSES, REPORTS, WINDOW_END, WINDOW_START

MANUAL_TRANSLATIONS = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "small_kitchen_appliances",
}


class Log:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, step: str, table: str, before: int, after: int, decision: str) -> None:
        self.rows.append({"step": len(self.rows) + 1, "table": table, "action": step,
                          "rows_before": before, "rows_after": after,
                          "rows_affected": before - after if before != after else 0, "decision": decision})

    def flag(self, step: str, table: str, rows: int, affected: int, decision: str) -> None:
        self.rows.append({"step": len(self.rows) + 1, "table": table, "action": step,
                          "rows_before": rows, "rows_after": rows, "rows_affected": affected, "decision": decision})


def read(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / name, **kw)


def build() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    log = Log()
    ts = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
          "order_delivered_customer_date", "order_estimated_delivery_date"]
    orders = read("olist_orders_dataset.csv", parse_dates=ts)
    items = read("olist_order_items_dataset.csv")
    pays = read("olist_order_payments_dataset.csv")
    reviews = read("olist_order_reviews_dataset.csv", parse_dates=["review_creation_date", "review_answer_timestamp"])
    customers = read("olist_customers_dataset.csv", dtype=str)
    products = read("olist_products_dataset.csv")
    trans = read("product_category_name_translation.csv")

    n = len(orders)
    orders = orders.sort_values("order_purchase_timestamp").drop_duplicates("order_id")
    log.add("Drop duplicate order_id", "orders", n, len(orders), "Order grain must be unique; keep earliest.")

    n = len(orders)
    orders["order_status"] = orders["order_status"].str.strip().str.lower()
    in_window = (orders.order_purchase_timestamp >= WINDOW_START) & (orders.order_purchase_timestamp < WINDOW_END)
    orders = orders[in_window]
    log.add("Keep purchases 2017-01-01 to 2018-08-31", "orders", n, len(orders),
            "Months outside the window are partial (data collection start/end) and distort MoM growth.")

    n = len(orders)
    orders = orders[~orders.order_status.isin(EXCLUDED_STATUSES)]
    log.add("Exclude canceled and unavailable orders", "orders", n, len(orders),
            "These orders generated no revenue; counting them would overstate demand.")

    # category: English name, two manual translations, 'unknown' when missing
    products = products.merge(trans, on="product_category_name", how="left")
    no_cat = products.product_category_name.isna().sum()
    manual = products.product_category_name.isin(MANUAL_TRANSLATIONS).sum()
    products["category"] = (products.product_category_name_english
                            .fillna(products.product_category_name.map(MANUAL_TRANSLATIONS))
                            .fillna("unknown"))
    log.flag("Translate two categories missing from the translation file", "products", len(products), int(manual),
             "pc_gamer and portateis_cozinha_e_preparadores_de_alimentos mapped by hand.")
    log.flag("Label products with no category as 'unknown'", "products", len(products), int(no_cat),
             "Kept: their revenue is real; dropping them would understate totals.")

    items = items.merge(products[["product_id", "category"]], on="product_id", how="left")
    items = items[items.order_id.isin(orders.order_id)].copy()

    n = len(orders)
    orders = orders[orders.order_id.isin(items.order_id)]
    log.add("Drop orders with no order items", "orders", n, len(orders),
            "No items means no revenue or category; these are data gaps, not sales.")

    n = len(reviews)
    reviews = (reviews.sort_values(["order_id", "review_answer_timestamp", "review_creation_date", "review_id"],
                                   ascending=[True, False, False, True], na_position="last")
               .drop_duplicates("order_id"))
    log.add("Keep the latest review per order", "order_reviews", n, len(reviews),
            "Some orders carry several reviews; the latest answer reflects the final experience.")

    # payments: one row per order, primary type = method that paid the most
    pays = pays.sort_values(["order_id", "payment_value", "payment_sequential"], ascending=[True, False, True])
    pay = pays.groupby("order_id").agg(payment_total=("payment_value", "sum"),
                                       primary_payment_type=("payment_type", "first"),
                                       max_installments=("payment_installments", "max"))

    agg = items.groupby("order_id").agg(n_items=("order_item_id", "size"), revenue=("price", "sum"),
                                        freight=("freight_value", "sum"), n_sellers=("seller_id", "nunique"))
    primary = (items.sort_values(["order_id", "price", "order_item_id"], ascending=[True, False, True])
               .drop_duplicates("order_id").set_index("order_id")["category"].rename("primary_category"))

    customers["customer_state"] = customers.customer_state.str.strip().str.upper()
    df = (orders.merge(customers[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id")
          .merge(agg, left_on="order_id", right_index=True)
          .merge(primary, left_on="order_id", right_index=True)
          .merge(pay, left_on="order_id", right_index=True, how="left")
          .merge(reviews[["order_id", "review_score"]], on="order_id", how="left"))

    df["purchase_month"] = df.order_purchase_timestamp.dt.to_period("M").dt.to_timestamp()
    df["is_delivered"] = (df.order_status == "delivered") & df.order_delivered_customer_date.notna()
    log.flag("Treat 'delivered' orders with no delivery date as not delivered", "orders", len(df),
             int(((df.order_status == "delivered") & df.order_delivered_customer_date.isna()).sum()),
             "Delivery time and lateness cannot be measured without the date.")
    df["delivery_days"] = np.where(df.is_delivered,
                                   (df.order_delivered_customer_date - df.order_purchase_timestamp).dt.total_seconds() / 86400,
                                   np.nan)
    df["delay_days"] = np.where(df.is_delivered,
                                (df.order_delivered_customer_date.dt.normalize() - df.order_estimated_delivery_date.dt.normalize()).dt.days,
                                np.nan)
    df["is_late"] = np.where(df.is_delivered, df.delay_days > 0, np.nan)
    log.flag("Flag (not drop) carrier pickup timestamps earlier than purchase", "orders", len(df),
             int((df.order_delivered_carrier_date < df.order_purchase_timestamp).sum()),
             "Timestamp noise in an unused field; customer delivery dates are consistent.")
    p999 = items.price.quantile(0.999)  # 99.9th percentile, also stored in facts.json data_quality
    log.flag("Keep high-price items above the 99.9th percentile", "order_items", len(items),
             int((items.price > p999).sum()),
             f"Prices up to R${items.price.max():,.0f} are plausible (furniture, electronics); not errors.")

    df = df.sort_values(["customer_unique_id", "order_purchase_timestamp", "order_id"])
    df["customer_order_seq"] = df.groupby("customer_unique_id").cumcount() + 1
    df = df.rename(columns={"order_purchase_timestamp": "purchase_ts"}).reset_index(drop=True)

    cols = ["order_id", "customer_unique_id", "purchase_ts", "purchase_month", "order_status", "customer_state",
            "n_items", "revenue", "freight", "n_sellers", "primary_category", "payment_total",
            "primary_payment_type", "max_installments", "is_delivered", "delivery_days", "delay_days",
            "is_late", "review_score", "customer_order_seq"]
    df = df[cols]
    items = items.merge(df[["order_id", "customer_unique_id", "purchase_month", "customer_state"]], on="order_id")
    log_df = pd.DataFrame(log.rows)

    df.to_parquet(DATA_PROCESSED / "orders_clean.parquet", index=False)
    items.to_parquet(DATA_PROCESSED / "items_clean.parquet", index=False)
    log_df.to_csv(REPORTS / "cleaning_log.csv", index=False)
    print(f"clean: {len(df):,} orders, {len(items):,} items, revenue R${df.revenue.sum():,.2f}; {len(log_df)} logged decisions")
    return df, items, log_df


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (pd.read_parquet(DATA_PROCESSED / "orders_clean.parquet"),
            pd.read_parquet(DATA_PROCESSED / "items_clean.parquet"))


if __name__ == "__main__":
    build()
