"""Build data/warehouse.duckdb from the raw CSVs and run the named KPI queries.

Runs sql/00..02 in order, then every `-- name:` block in sql/03_kpi_queries.sql,
saving each result to reports/sql_outputs/<name>.csv.
"""
from __future__ import annotations

import re
import sys

import duckdb
import pandas as pd

from src.config import DATA_RAW, DB_PATH, SQL_DIR, SQL_OUT

BUILD_FILES = ["00_schema.sql", "01_staging_clean.sql", "02_analysis_views.sql"]


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def named_queries(path=SQL_DIR / "03_kpi_queries.sql") -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.M)
    # blocks = [preamble, name1, body1, name2, body2, ...]
    return {blocks[i]: blocks[i + 1].strip().rstrip(";") for i in range(1, len(blocks), 2)}


def query(name: str) -> pd.DataFrame:
    with connect(read_only=True) as con:
        return con.execute(named_queries()[name]).df()


def build() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    raw = DATA_RAW.as_posix()
    with connect() as con:
        for f in BUILD_FILES:
            sql = (SQL_DIR / f).read_text(encoding="utf-8").replace("${RAW}", raw)
            con.execute(sql)
            print(f"warehouse: ran {f}")
        for name, sql in named_queries().items():
            con.execute(sql).df().to_csv(SQL_OUT / f"{name}.csv", index=False)
        counts = con.execute("""
            SELECT 'raw.orders' t, COUNT(*) n FROM raw.orders UNION ALL
            SELECT 'fact_order_items', COUNT(*) FROM fact_order_items UNION ALL
            SELECT 'fact_orders', COUNT(*) FROM fact_orders""").fetchall()
    for t, n in counts:
        print(f"warehouse: {t:<18} {n:>9,}")
    print(f"warehouse: saved {len(named_queries())} KPI query outputs to {SQL_OUT}")


if __name__ == "__main__":
    build()
    sys.exit(0)
