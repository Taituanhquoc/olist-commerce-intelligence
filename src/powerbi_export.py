"""Export the star schema and helper tables to powerbi/export/*.csv for Power BI Desktop."""
from __future__ import annotations

from src.config import ROOT
from src.warehouse import connect

OUT = ROOT / "powerbi" / "export"

QUERIES = {
    "fact_order_items": "SELECT * FROM fact_order_items",
    "fact_orders": """
        SELECT *, CASE
            WHEN NOT is_delivered THEN NULL
            WHEN delay_days <= -15 THEN '1. 15+ days early' WHEN delay_days <= -8 THEN '2. 8-14 days early'
            WHEN delay_days <= -1 THEN '3. 1-7 days early'  WHEN delay_days = 0 THEN '4. On the promised day'
            WHEN delay_days <= 3 THEN '5. 1-3 days late'    WHEN delay_days <= 7 THEN '6. 4-7 days late'
            ELSE '7. 8+ days late' END AS delay_bucket
        FROM fact_orders""",
    "dim_date": "SELECT * FROM dim_date",
    "dim_customer": "SELECT * FROM dim_customer",
    "dim_product": "SELECT * FROM dim_product",
    "dim_seller": "SELECT * FROM dim_seller",
    "rfm_segments": "SELECT * FROM v_rfm_segments",
    "cohort_retention": "SELECT * FROM v_cohort_retention",
    "delivery_review": "SELECT * FROM v_delivery_review",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with connect(read_only=True) as con:
        for name, sql in QUERIES.items():
            con.execute(f"COPY ({sql}) TO '{(OUT / f'{name}.csv').as_posix()}' (HEADER, DELIMITER ',')")
            print(f"powerbi_export: {name}.csv")


if __name__ == "__main__":
    main()
