"""Build dashboard/index.html: one self-contained file (Plotly inlined, data inlined).

The page works offline from file:// and is copied to docs/index.html for GitHub Pages.
Filterable data ships as small pre-aggregated cubes (month x category x state); the JS
sums them on the fly, so every KPI on the page is additive and matches facts.json.
"""
from __future__ import annotations

import json
import shutil
from datetime import date

import numpy as np
import pandas as pd
from plotly.offline import get_plotlyjs

from src import facts
from src.clean import load
from src.config import DASHBOARD, DOCS, REPO_URL, SQL_OUT
from src.fmt import brl, pct, sig

BUCKETS = ["15+ days early", "8-14 days early", "1-7 days early", "On the promised day",
           "1-3 days late", "4-7 days late", "8+ days late"]


def bucket(delay: pd.Series) -> pd.Series:
    # same edges as v_delivery_review in sql/02_analysis_views.sql
    return pd.cut(delay, [-np.inf, -15, -8, -1, 0, 3, 7, np.inf], labels=False).astype("Int64")


def cube(df: pd.DataFrame, keys: list[str], vals: dict[str, tuple], decimals: dict[str, int]) -> list[list]:
    g = df.groupby(keys, observed=True).agg(**vals).reset_index()
    for c, d in decimals.items():
        g[c] = g[c].round(d)
    return [[(int(v) if float(v).is_integer() else float(v)) for v in row] for row in g.values.tolist()]


def build() -> dict:
    orders, items = load()
    f = facts.read()["analysis"]
    months = sorted(orders.purchase_month.dt.strftime("%Y-%m").unique())
    cats = sorted(set(items.category) | set(orders.primary_category))
    states = sorted(orders.customer_state.unique())
    pay_types = sorted(orders.primary_payment_type.fillna("unknown").unique())
    mi = {m: i for i, m in enumerate(months)}
    ci = {c: i for i, c in enumerate(cats)}
    si = {s: i for i, s in enumerate(states)}
    pi = {p: i for i, p in enumerate(pay_types)}

    o = orders.copy()
    o["m"] = o.purchase_month.dt.strftime("%Y-%m").map(mi)
    o["c"] = o.primary_category.map(ci)
    o["s"] = o.customer_state.map(si)
    o["late"] = (o.is_late.fillna(False).astype(bool) & o.is_delivered).astype(int)
    o["deliv"] = o.is_delivered.astype(int)
    o["days"] = o.delivery_days.fillna(0)
    o["rs"] = o.review_score.fillna(0)
    o["rc"] = o.review_score.notna().astype(int)
    o["new"] = (o.customer_order_seq == 1).astype(int)
    oc = cube(o, ["m", "c", "s"], {"orders": ("order_id", "size"), "revenue": ("revenue", "sum"), "delivered": ("deliv", "sum"),
                                   "late": ("late", "sum"), "days": ("days", "sum"), "rs": ("rs", "sum"), "rc": ("rc", "sum"),
                                   "new": ("new", "sum"), "freight": ("freight", "sum")},
              {"revenue": 2, "days": 3, "freight": 2})

    it = items.copy()
    it["m"] = it.purchase_month.dt.strftime("%Y-%m").map(mi)
    it["c"] = it.category.map(ci)
    it["s"] = it.customer_state.map(si)
    ic = cube(it, ["m", "c", "s"], {"revenue": ("price", "sum"), "items": ("order_item_id", "size"),
                                    "freight": ("freight_value", "sum")}, {"revenue": 2, "freight": 2})

    d = o[o.is_delivered & o.review_score.notna()].copy()
    d["b"] = bucket(d.delay_days)
    d["low"] = (d.review_score <= 2).astype(int)
    dc = cube(d, ["m", "c", "s", "b"], {"n": ("order_id", "size"), "rs": ("review_score", "sum"), "low": ("low", "sum")}, {})

    o["p"] = o.primary_payment_type.fillna("unknown").map(pi)
    pc = cube(o, ["m", "c", "s", "p"], {"orders": ("order_id", "size"), "revenue": ("revenue", "sum")}, {"revenue": 2})

    sp = items.groupby("seller_id").price.sum().sort_values(ascending=False)
    cum = (sp.cumsum() / sp.sum()).values
    pts = np.unique(np.linspace(0, len(sp) - 1, 200).astype(int))
    pareto = {"x": [round((i + 1) / len(sp), 4) for i in pts], "y": [round(float(cum[i]), 4) for i in pts]}

    order_ = ["Champions", "Loyal", "Promising", "New Customers", "At-Risk", "Hibernating", "Lost"]
    seg = f["rfm"]["segments"]
    rfm = {k: [seg[s][k] for s in order_] for k in
           ["customers", "customer_share", "revenue", "revenue_share", "avg_revenue", "avg_recency_days"]}
    rfm["segment"] = order_

    coh = pd.read_csv(SQL_OUT / "cohort_retention.csv", parse_dates=["cohort_month"])
    mat = coh[(coh.months_since_first >= 1) & (coh.months_since_first <= 12)].pivot(
        index="cohort_month", columns="months_since_first", values="retention_rate")
    cohort = {"x": [int(c) for c in mat.columns], "y": [d_.strftime("%Y-%m") for d_ in mat.index],
              "z": [[None if pd.isna(v) else round(float(v), 5) for v in row] for row in mat.values]}

    k, c = f["kpi"], f["cohort"]
    customer_kpis = [["Customers", f"{k['customers']:,}"], ["Repeat purchase rate", pct(k["repeat_rate"], 2)],
                     ["Month-1 retention", pct(c["month1_retention"], 2)],
                     ["Revenue from repeat orders", pct(c["repeat_revenue_share"])],
                     ["High-value one-time buyers", f"{f['rfm']['high_value_one_timers']:,}"]]

    data = {"months": months, "categories": cats, "states": states, "payTypes": pay_types, "buckets": BUCKETS,
            "oc": oc, "ic": ic, "dc": dc, "pc": pc, "pareto": pareto, "rfm": rfm, "cohort": cohort,
            "customerKpis": customer_kpis}

    t = f["trend"]
    headline = (f"{brl(k['revenue'])} of item revenue from {k['orders']:,} orders. Jan-Aug revenue grew "
                f"{pct(t['yoy_revenue_growth'], 0)} year on year, but the 2018 monthly run-rate is flat, only "
                f"{pct(k['repeat_rate'])} of customers ever order twice, and late orders average "
                f"{sig(f['delivery']['late_avg_review'])} stars against {sig(f['delivery']['ontime_avg_review'])} on time.")
    html = (DASHBOARD.parent / "template.html").read_text(encoding="utf-8")
    html = (html.replace("{{HEADLINE}}", headline).replace("{{REPO_URL}}", REPO_URL)
            .replace("{{GENERATED}}", date.today().isoformat())
            .replace("/*DATA*/", json.dumps(data, separators=(",", ":")))
            .replace("/*PLOTLY*/", get_plotlyjs()))
    DASHBOARD.write_text(html, encoding="utf-8")
    DOCS.mkdir(exist_ok=True)
    shutil.copy2(DASHBOARD, DOCS / "index.html")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    # totals the tests compare against facts.json
    checks = {"oc_revenue": float(sum(r[4] for r in oc)), "oc_orders": int(sum(r[3] for r in oc)),
              "ic_revenue": float(sum(r[3] for r in ic)), "oc_late": int(sum(r[6] for r in oc)),
              "oc_delivered": int(sum(r[5] for r in oc)), "size_mb": round(len(html.encode()) / 1e6, 2),
              "headline": headline}
    facts.update("dashboard", checks)
    print(f"dashboard: wrote {DASHBOARD.name} ({checks['size_mb']} MB), cubes oc={len(oc)} ic={len(ic)} dc={len(dc)} pc={len(pc)}")
    return checks


if __name__ == "__main__":
    build()
