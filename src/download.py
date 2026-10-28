"""Fetch the Olist CSVs into data/raw, trying sources in order and validating each one.

Source order: (a) Kaggle via kagglehub (works anonymously for this public dataset),
(b) a public GitHub mirror of the original files. A source is accepted only if every
expected file exists, has the expected columns, a row count within 20% of the published
size, and key columns that are not mostly null.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from src.config import DATA_RAW

EXPECTED = {
    # file: (expected rows, required columns, key column)
    "olist_customers_dataset.csv": (99441, ["customer_id", "customer_unique_id", "customer_state"], "customer_id"),
    "olist_geolocation_dataset.csv": (1000163, ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"], "geolocation_zip_code_prefix"),
    "olist_order_items_dataset.csv": (112650, ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"], "order_id"),
    "olist_order_payments_dataset.csv": (103886, ["order_id", "payment_type", "payment_installments", "payment_value"], "order_id"),
    "olist_order_reviews_dataset.csv": (99224, ["review_id", "order_id", "review_score"], "order_id"),
    "olist_orders_dataset.csv": (99441, ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_estimated_delivery_date"], "order_id"),
    "olist_products_dataset.csv": (32951, ["product_id", "product_category_name"], "product_id"),
    "olist_sellers_dataset.csv": (3095, ["seller_id", "seller_state"], "seller_id"),
    "product_category_name_translation.csv": (71, ["product_category_name", "product_category_name_english"], "product_category_name"),
}

KAGGLE_HANDLE = "olistbr/brazilian-ecommerce"
MIRROR_BASE = "https://raw.githubusercontent.com/ductransponster/olist-brazilian-ecommerce/main/data/original_data/"
LICENCE = "CC BY-NC-SA 4.0 (as published by Olist on Kaggle)"


def validate(folder: Path) -> list[str]:
    problems = []
    for name, (rows, cols, key) in EXPECTED.items():
        f = folder / name
        if not f.exists():
            problems.append(f"{name}: missing")
            continue
        df = pd.read_csv(f, dtype=str)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            problems.append(f"{name}: missing columns {missing}")
            continue
        if not (0.8 * rows <= len(df) <= 1.2 * rows):
            problems.append(f"{name}: {len(df)} rows, expected about {rows}")
        if df[key].isna().mean() > 0.5:
            problems.append(f"{name}: key column {key} mostly null")
    return problems


def from_kaggle(dest: Path) -> str:
    import kagglehub

    src = Path(kagglehub.dataset_download(KAGGLE_HANDLE))
    for name in EXPECTED:
        shutil.copy2(src / name, dest / name)
    return f"https://www.kaggle.com/datasets/{KAGGLE_HANDLE}"


def from_mirror(dest: Path) -> str:
    for name in EXPECTED:
        r = requests.get(MIRROR_BASE + name, timeout=120)
        r.raise_for_status()
        (dest / name).write_bytes(r.content)
    return MIRROR_BASE


def main() -> int:
    meta_path = DATA_RAW / "_source.json"
    if meta_path.exists() and not validate(DATA_RAW):
        print("download: raw data already present and valid")
        return 0
    for label, fn in (("kaggle", from_kaggle), ("github-mirror", from_mirror)):
        for attempt in range(1, 4):
            try:
                url = fn(DATA_RAW)
                problems = validate(DATA_RAW)
                if problems:
                    raise ValueError("; ".join(problems))
                meta = {"source": label, "url": url, "licence": LICENCE,
                        "retrieved": date.today().isoformat(), "files": list(EXPECTED)}
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
                print(f"download: OK from {label} ({url})")
                return 0
            except Exception as exc:  # noqa: BLE001 - log and try again / next source
                print(f"download: {label} attempt {attempt} failed: {exc}", file=sys.stderr)
    print("download: every source failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
