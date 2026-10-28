"""Core analysis for the seven business questions. Writes the bulk of reports/facts.json.

Every number used later in the README, insights, dashboard text or resume is computed
here (or in eda.py) and stored in facts.json; nothing downstream does its own maths.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

from src import facts
from src.clean import load
from src.config import SNAPSHOT_DATE, SQL_OUT
from src.plotstyle import CRITICAL, INK_2, SERIES, brl, save

# Assumptions behind the impact estimates (stored in facts.json so every figure is traceable).
ASSUMPTIONS = {
    "repeat_lift_pp": 1.0,           # second-purchase programme lifts repeat rate by 1 percentage point
    "repeat_lift_low_pp": 0.5,
    "repeat_lift_high_pp": 2.0,
    "basket_lift_pp": 2.0,           # cross-sell lifts the share of multi-item orders by 2 points
    "min_state_orders": 300,         # states need this many delivered orders to be ranked
    # reporting constants, kept here so every number printed in the docs traces to facts.json
    "ci_level_pct": 95, "alpha": 0.05, "p_floor": 0.001, "repeat_window_days": 180,
    "top_n_chart": 15, "dashboard_min_state_orders": 100, "months_per_year": 12,
}


def ntile(n_rows: int, n: int) -> np.ndarray:
    """Bucket numbers with SQL NTILE semantics: the first (n_rows % n) buckets get one extra row."""
    base, extra = divmod(n_rows, n)
    sizes = [base + 1 if i < extra else base for i in range(n)]
    return np.repeat(np.arange(1, n + 1), sizes)


def segment(row) -> str:
    if row.frequency >= 2:
        return "Champions" if row.r_score >= 4 else "Loyal"
    if row.r_score >= 4:
        return "Promising" if row.m_score >= 4 else "New Customers"
    if row.r_score >= 2:
        return "At-Risk" if row.m_score >= 4 else "Hibernating"
    return "Lost"


def rfm_table(orders: pd.DataFrame) -> pd.DataFrame:
    snap = pd.Timestamp(SNAPSHOT_DATE)
    c = orders.groupby("customer_unique_id").agg(last=("purchase_ts", "max"), frequency=("order_id", "size"),
                                                 monetary=("revenue", "sum")).reset_index()
    c["recency_days"] = (snap - c["last"].dt.normalize()).dt.days
    c = c.sort_values(["recency_days", "customer_unique_id"], ascending=[False, True])
    c["r_score"] = ntile(len(c), 5)
    c = c.sort_values(["monetary", "customer_unique_id"], ascending=[True, True])
    c["m_score"] = ntile(len(c), 5)
    c["f_score"] = np.select([c.frequency == 1, c.frequency == 2], [1, 4], 5)
    c["segment"] = c.apply(segment, axis=1)
    return c


def run() -> dict:
    orders, items = load()
    f: dict = {"assumptions": ASSUMPTIONS}
    delivered = orders[orders.is_delivered]
    late_mask = delivered.is_late.astype(bool)

    # ------------------------------------------------------------------ headline KPIs
    per_cust = orders.groupby("customer_unique_id").size()
    kpi = {
        "revenue": orders.revenue.sum(), "orders": len(orders), "customers": per_cust.size,
        "aov": orders.revenue.sum() / len(orders), "freight": orders.freight.sum(),
        "freight_to_revenue": orders.freight.sum() / orders.revenue.sum(),
        "items_per_order": orders.n_items.mean(), "repeat_rate": (per_cust >= 2).mean(),
        "repeat_customers": int((per_cust >= 2).sum()), "one_time_share": (per_cust == 1).mean(), "on_time_rate": 1 - late_mask.mean(),
        "late_rate": late_mask.mean(), "late_orders": int(late_mask.sum()), "delivered_orders": len(delivered),
        "avg_delivery_days": delivered.delivery_days.mean(), "avg_review": orders.review_score.mean(),
        "months": orders.purchase_month.nunique(), "categories": items.category.nunique(),
        "sellers": items.seller_id.nunique(), "states": orders.customer_state.nunique(),
    }
    f["kpi"] = kpi

    sql = pd.read_csv(SQL_OUT / "headline_kpis.csv").iloc[0]
    f["crosscheck"] = {"sql_revenue": sql.revenue, "python_revenue": kpi["revenue"],
                       "sql_orders": int(sql.orders), "python_orders": kpi["orders"],
                       "sql_repeat_rate": sql.repeat_rate, "python_repeat_rate": kpi["repeat_rate"],
                       "sql_on_time_rate": sql.on_time_rate, "python_on_time_rate": kpi["on_time_rate"]}

    # ------------------------------------------------------------------ Q1 trend
    orders["year"] = orders.purchase_month.dt.year
    ja = orders[orders.purchase_month.dt.month <= 8].groupby("year").agg(revenue=("revenue", "sum"), orders=("order_id", "size"))
    ja["aov"] = ja.revenue / ja.orders
    m = orders.groupby("purchase_month").agg(revenue=("revenue", "sum"), orders=("order_id", "size"))
    m["mom"] = m.revenue.pct_change()
    m18 = m.loc["2018"]
    slope = np.polyfit(np.arange(len(m18)), m18.revenue.values, 1)[0]
    annual_rev_2018 = m18.revenue.mean() * 12
    f["trend"] = {
        "revenue_2017_jan_aug": ja.loc[2017, "revenue"], "revenue_2018_jan_aug": ja.loc[2018, "revenue"],
        "orders_2017_jan_aug": int(ja.loc[2017, "orders"]), "orders_2018_jan_aug": int(ja.loc[2018, "orders"]),
        "yoy_revenue_growth": ja.loc[2018, "revenue"] / ja.loc[2017, "revenue"] - 1,
        "yoy_orders_growth": ja.loc[2018, "orders"] / ja.loc[2017, "orders"] - 1,
        "yoy_aov_growth": ja.loc[2018, "aov"] / ja.loc[2017, "aov"] - 1,
        "aov_2017_jan_aug": ja.loc[2017, "aov"], "aov_2018_jan_aug": ja.loc[2018, "aov"],
        "avg_mom_growth_2017": m.loc["2017-02":"2017-12", "mom"].mean(),
        "avg_mom_growth_2018": m.loc["2018", "mom"].mean(),
        "trend_slope_2018_per_month": slope, "trend_slope_2018_pct": slope / m18.revenue.mean(),
        "avg_monthly_revenue_2018": m18.revenue.mean(), "avg_monthly_orders_2018": m18.orders.mean(),
        "annualised_revenue_2018": annual_rev_2018,
        "nov_2017_revenue": m.loc["2017-11", "revenue"].iloc[0],
        "nov_2017_mom": m.loc["2017-11", "mom"].iloc[0],
    }

    # ------------------------------------------------------------------ Q2 categories & sellers
    cat = items.groupby("category").agg(revenue=("price", "sum"), freight=("freight_value", "sum")).sort_values("revenue", ascending=False)
    cat["share"] = cat.revenue / cat.revenue.sum()
    cat["rank"] = np.arange(1, len(cat) + 1)
    cat["freight_ratio"] = cat.freight / cat.revenue
    top5 = [{"category": k, "revenue": r.revenue, "share": r.share} for k, r in cat.head(5).iterrows()]
    seller = items.groupby("seller_id").price.sum().reset_index().sort_values(["price", "seller_id"], ascending=[False, True])
    seller["decile"] = ntile(len(seller), 10)
    f["category"] = {
        "n_categories": len(cat), "top10_share": cat.head(10).share.sum(),
        "bottom_half_share": cat[cat["rank"] > len(cat) // 2].share.sum(),
        "top5": top5, "top5_share": cat.head(5).share.sum(),
        "n_sellers": len(seller),
        "top10pct_sellers_share": seller[seller.decile == 1].price.sum() / seller.price.sum(),
        "top20pct_sellers_share": seller[seller.decile <= 2].price.sum() / seller.price.sum(),
    }
    s = seller.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(np.arange(1, len(s) + 1) / len(s) * 100, s.price.cumsum() / s.price.sum() * 100, color=SERIES[0])
    ax.axvline(10, color=INK_2, linewidth=0.8)
    ax.text(11, 40, f"top 10% of sellers = {f['category']['top10pct_sellers_share']:.0%} of revenue", fontsize=9, color=INK_2)
    ax.set_title(f"Revenue is concentrated: the top 10% of {len(s):,} sellers earn "
                 f"{f['category']['top10pct_sellers_share']:.0%} of it", fontsize=11)
    ax.set_xlabel("Sellers, ranked by revenue (cumulative %)")
    ax.set_ylabel("Cumulative revenue (%)")
    save(fig, "12_seller_pareto", "Takeaway: losing a few large sellers would hurt more than any category trend.")

    # ------------------------------------------------------------------ Q3 RFM
    rfm = rfm_table(orders)
    seg = rfm.groupby("segment").agg(customers=("customer_unique_id", "size"), revenue=("monetary", "sum"),
                                     avg_revenue=("monetary", "mean"), avg_recency_days=("recency_days", "mean"))
    seg["customer_share"] = seg.customers / seg.customers.sum()
    seg["revenue_share"] = seg.revenue / seg.revenue.sum()
    seg = seg.sort_values("revenue", ascending=False)
    rfm[["customer_unique_id", "recency_days", "frequency", "monetary", "r_score", "f_score", "m_score", "segment"]] \
        .to_csv(SQL_OUT.parent / "rfm_customers.csv", index=False)
    hv = seg.loc[["Promising", "At-Risk"]]
    f["rfm"] = {
        "segments": {k: {c: r[c] for c in ["customers", "customer_share", "revenue", "revenue_share", "avg_revenue", "avg_recency_days"]}
                     for k, r in seg.iterrows()},
        "high_value_one_timers": int(hv.customers.sum()),
        "high_value_one_timers_customer_share": hv.customer_share.sum(),
        "high_value_one_timers_revenue_share": hv.revenue_share.sum(),
        "repeat_segments_customer_share": seg.loc[["Champions", "Loyal"]].customer_share.sum(),
        "repeat_segments_revenue_share": seg.loc[["Champions", "Loyal"]].revenue_share.sum(),
    }
    order_ = ["Champions", "Loyal", "Promising", "New Customers", "At-Risk", "Hibernating", "Lost"]
    sg = seg.reindex(order_)
    x = np.arange(len(order_))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(x - 0.2, sg.customer_share * 100, 0.38, label="Share of customers", color=SERIES[0])
    ax.bar(x + 0.2, sg.revenue_share * 100, 0.38, label="Share of revenue", color=SERIES[1])
    ax.set_xticks(x, order_)
    ax.set_ylabel("%")
    ax.legend(loc="upper right")
    ax.set_title(f"Promising and At-Risk one-time buyers are {hv.customer_share.sum():.0%} of customers but "
                 f"{hv.revenue_share.sum():.0%} of revenue", fontsize=11)
    save(fig, "07_rfm_segments", "Takeaway: the second-purchase campaign should target these two high-value groups first.")

    # ------------------------------------------------------------------ Q4 cohorts & repeat
    first = orders[orders.customer_order_seq == 1][["customer_unique_id", "purchase_month", "purchase_ts", "is_late", "review_score", "is_delivered"]]
    first = first.rename(columns={"purchase_month": "cohort", "purchase_ts": "t0"})
    act = orders[["customer_unique_id", "purchase_month"]].drop_duplicates().merge(first[["customer_unique_id", "cohort"]], on="customer_unique_id")
    act["k"] = (act.purchase_month.dt.year - act.cohort.dt.year) * 12 + (act.purchase_month.dt.month - act.cohort.dt.month)
    mat = act.groupby(["cohort", "k"]).size().unstack(fill_value=0)
    size = mat[0]
    ret = mat.div(size, axis=0)
    observed = ret.columns.values[None, :] <= ((pd.Timestamp("2018-08-01").year - ret.index.year) * 12
                                              + (8 - ret.index.month)).values[:, None]
    ret = ret.where(observed)
    m1 = (mat[1] * observed[:, 1]).sum() / size[observed[:, 1]].sum()
    second = orders[orders.customer_order_seq == 2][["customer_unique_id", "purchase_ts"]].rename(columns={"purchase_ts": "t1"})
    fr = first.merge(second, on="customer_unique_id", how="left")
    eligible = fr[fr.cohort <= "2018-02-01"]
    within180 = ((eligible.t1 - eligible.t0).dt.days <= ASSUMPTIONS["repeat_window_days"]).mean()
    repeat_orders = orders[orders.customer_order_seq >= 2]
    f["cohort"] = {
        "month1_retention": m1, "repeat_within_180d": within180, "eligible_customers_180d": len(eligible),
        "repeat_orders": len(repeat_orders), "repeat_revenue_share": repeat_orders.revenue.sum() / orders.revenue.sum(),
        "avg_repeat_order_revenue": repeat_orders.revenue.mean(),
        "max_cell_retention_after_m0": np.nanmax(ret.iloc[:, 1:].values),
    }
    fig, ax = plt.subplots(figsize=(10, 6))
    show = ret.iloc[:, 1:13] * 100
    im = ax.imshow(show.values, cmap="Blues", aspect="auto", vmin=0, vmax=max(0.6, np.nanmax(show.values)))
    ax.set_xticks(range(show.shape[1]), [str(c) for c in show.columns])
    ax.set_yticks(range(len(show)), [d.strftime("%Y-%m") for d in show.index])
    ax.set_xlabel("Months since first purchase")
    ax.set_ylabel("Cohort (first-purchase month)")
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("% of cohort ordering again that month")
    ax.set_title(f"No cohort ever retains more than {np.nanmax(ret.iloc[:, 1:].values):.1%} of customers in any later month", fontsize=11)
    save(fig, "08_cohort_heatmap", f"Takeaway: month-1 retention is {m1:.2%}; only {within180:.1%} of customers buy again within 180 days.")

    # ------------------------------------------------------------------ Q5 late delivery vs review
    rv = delivered.dropna(subset=["review_score"])
    late_s = rv[rv.is_late.astype(bool)].review_score
    on_s = rv[~rv.is_late.astype(bool)].review_score
    u, p = stats.mannwhitneyu(late_s, on_s, alternative="two-sided")
    rbc = 2 * u / (len(late_s) * len(on_s)) - 1
    diff = on_s.mean() - late_s.mean()
    se = np.sqrt(on_s.var() / len(on_s) + late_s.var() / len(late_s))
    bucket = pd.read_csv(SQL_OUT / "delivery_review.csv")
    b8 = bucket[bucket.delay_bucket.str.startswith("7.")].iloc[0]
    f["delivery"] = {
        "late_avg_review": late_s.mean(), "ontime_avg_review": on_s.mean(), "review_gap": diff,
        "review_gap_ci_low": diff - 1.96 * se, "review_gap_ci_high": diff + 1.96 * se,
        "n_late_reviewed": len(late_s), "n_ontime_reviewed": len(on_s), "n_reviewed": len(late_s) + len(on_s),
        "mwu_u": u, "mwu_p_value": p, "rank_biserial": rbc,
        "late_low_review_share": (late_s <= 2).mean(), "ontime_low_review_share": (on_s <= 2).mean(),
        "late8_avg_review": b8.avg_review, "late8_low_review_share": b8.low_review_share, "late8_orders": int(b8.orders),
    }
    fig, ax = plt.subplots(figsize=(9, 4))
    labels = bucket.delay_bucket.str.slice(3)
    colors = [SERIES[0] if not str(b).startswith(("5", "6", "7")) else CRITICAL for b in bucket.delay_bucket]
    ax.bar(labels, bucket.avg_review, color=colors, width=0.6)
    for i, v in enumerate(bucket.avg_review):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=9, color=INK_2)
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average review score")
    ax.tick_params(axis="x", labelsize=8)
    ax.set_title(f"Reviews collapse once an order is late: {on_s.mean():.2f} on time vs {late_s.mean():.2f} late "
                 f"(Mann-Whitney p < 0.001)", fontsize=11)
    save(fig, "09_delay_vs_review", f"Takeaway: 8+ days late averages {b8.avg_review:.2f} stars; {b8.low_review_share:.0%} of those reviews are 1-2 stars.")

    # late first order vs coming back
    fd = fr[fr.is_delivered.astype(bool)].copy()
    fd["repeat"] = fd.t1.notna()
    g = fd.groupby(fd.is_late.astype(bool)).repeat.agg(["sum", "count", "mean"])
    z, pz = proportions_ztest(g["sum"].values, g["count"].values)
    f["retention_vs_delivery"] = {
        "repeat_rate_ontime_first": g.loc[False, "mean"], "repeat_rate_late_first": g.loc[True, "mean"],
        "n_ontime_first": int(g.loc[False, "count"]), "n_late_first": int(g.loc[True, "count"]),
        "gap_pp": (g.loc[False, "mean"] - g.loc[True, "mean"]) * 100, "z": z, "p_value": pz,
    }

    # ------------------------------------------------------------------ Q6 states
    st = delivered.groupby("customer_state").agg(delivered_orders=("order_id", "size"),
                                                 late_rate=("is_late", lambda s: s.astype(bool).mean()),
                                                 late_orders=("is_late", lambda s: s.astype(bool).sum()),
                                                 avg_delivery_days=("delivery_days", "mean"),
                                                 avg_review=("review_score", "mean"))
    ranked = st[st.delivered_orders >= ASSUMPTIONS["min_state_orders"]].sort_values("late_rate", ascending=False)
    target = ranked[ranked.late_rate > kpi["late_rate"]]
    f["state"] = {
        "worst5": [{"state": k, **{c: r[c] for c in ["late_rate", "delivered_orders", "avg_delivery_days", "avg_review"]}}
                   for k, r in ranked.head(5).iterrows()],
        "ranked_states": len(ranked),
        "target_states": list(target.index), "n_target_states": len(target),
        "target_late_orders": int(target.late_orders.sum()),
        "target_share_of_late": target.late_orders.sum() / kpi["late_orders"],
        "target_delivered_orders": int(target.delivered_orders.sum()),
        "target_share_of_delivered": target.delivered_orders.sum() / kpi["delivered_orders"],
        "target_late_rate": target.late_orders.sum() / target.delivered_orders.sum(),
        "rj_late_orders": int(st.loc["RJ", "late_orders"]), "rj_late_rate": st.loc["RJ", "late_rate"],
        "rj_share_of_late": st.loc["RJ", "late_orders"] / kpi["late_orders"],
        "sp_late_rate": st.loc["SP", "late_rate"], "sp_late_orders": int(st.loc["SP", "late_orders"]),
        "most_late_orders_state": st.late_orders.idxmax(), "sp_avg_delivery_days": st.loc["SP", "avg_delivery_days"],
        "fastest_state": st.avg_delivery_days.idxmin(), "slowest_ranked_state": ranked.avg_delivery_days.idxmax(),
        "slowest_ranked_days": ranked.avg_delivery_days.max(),
    }
    top = ranked.head(15)[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top.index, top.late_rate * 100, color=[CRITICAL if s in target.index else SERIES[0] for s in top.index], height=0.65)
    ax.axvline(kpi["late_rate"] * 100, color=INK_2, linewidth=1)
    ax.text(kpi["late_rate"] * 100 + 0.3, 0, f"national {kpi['late_rate']:.1%}", fontsize=9, color=INK_2)
    ax.set_xlabel("Late-delivery rate (%)")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"{len(target)} states run above the national late rate: {f['state']['target_share_of_delivered']:.0%} of "
                 f"deliveries, {f['state']['target_share_of_late']:.0%} of late orders", fontsize=11)
    save(fig, "10_state_late_rate", f"Takeaway: fixing logistics in these {len(target)} states addresses "
                                    f"{f['state']['target_share_of_late']:.0%} of late deliveries.")

    # ------------------------------------------------------------------ Q7 payments
    pm = orders.groupby(orders.primary_payment_type.fillna("unknown")).agg(orders=("order_id", "size"), revenue=("revenue", "sum"),
                                                                            inst=("max_installments", "mean"))
    pm["share"] = pm.orders / pm.orders.sum()
    pm["aov"] = pm.revenue / pm.orders
    cc = orders[orders.primary_payment_type == "credit_card"].copy()
    cc["band"] = pd.cut(cc.max_installments, [-1, 1, 3, 6, 100], labels=["1", "2-3", "4-6", "7+"])
    ib = cc.groupby("band", observed=True).agg(orders=("order_id", "size"), aov=("revenue", "mean"))
    f["payment"] = {
        "credit_card_share": pm.loc["credit_card", "share"], "boleto_share": pm.loc["boleto", "share"],
        "voucher_share": pm.loc["voucher", "share"], "debit_card_share": pm.loc["debit_card", "share"],
        "aov_credit_card": pm.loc["credit_card", "aov"], "aov_boleto": pm.loc["boleto", "aov"],
        "cc_avg_installments": pm.loc["credit_card", "inst"],
        "aov_single_payment": ib.loc["1", "aov"], "aov_7plus_installments": ib.loc["7+", "aov"],
        "share_cc_7plus": ib.loc["7+", "orders"] / ib.orders.sum(),
        "spearman_installments_value": stats.spearmanr(cc.max_installments, cc.revenue).statistic,
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(ib.index.astype(str), ib.aov, color=SERIES[0], width=0.6)
    for i, v in enumerate(ib.aov):
        ax.text(i, v + 4, brl(v), ha="center", fontsize=9, color=INK_2)
    ax.set_xlabel("Credit-card installments")
    ax.set_ylabel("Average order value (R$)")
    ax.set_title(f"Order value rises with installments: {brl(ib.loc['1', 'aov'])} single payment vs "
                 f"{brl(ib.loc['7+', 'aov'])} at 7+", fontsize=11)
    save(fig, "11_installments_aov", "Takeaway: installments enable big baskets; this is a correlation, so test before acting on it.")

    # ------------------------------------------------------------------ impact estimates
    annual_new = facts.read()["eda"]["avg_new_customers_2018"] * 12
    rep_val = f["cohort"]["avg_repeat_order_revenue"]
    a1 = {k: annual_new * ASSUMPTIONS[k] / 100 * rep_val for k in ["repeat_lift_pp", "repeat_lift_low_pp", "repeat_lift_high_pp"]}
    # A2: bring target states down to the national late rate
    d18 = delivered[delivered.purchase_month >= "2018-01-01"]
    t18 = d18[d18.customer_state.isin(target.index)]
    annual_target_delivered = len(t18) / 8 * 12
    t18_late = t18.is_late.astype(bool).mean()
    avoided = annual_target_delivered * (t18_late - kpi["late_rate"])
    reviewed_share = rv.shape[0] / delivered.shape[0]
    annual_reviews = len(d18) / 8 * 12 * reviewed_share
    review_uplift = avoided * reviewed_share * diff / annual_reviews
    a2_rev = avoided * (f["retention_vs_delivery"]["gap_pp"] / 100) * rep_val
    # A3: basket building
    multi = orders[orders.n_items > 1]
    top_item = items.groupby("order_id").price.max()
    addon = (multi.set_index("order_id").revenue - top_item.reindex(multi.order_id)).mean()
    annual_orders = f["trend"]["avg_monthly_orders_2018"] * 12
    a3 = annual_orders * ASSUMPTIONS["basket_lift_pp"] / 100 * addon
    total = a1["repeat_lift_pp"] + a2_rev + a3
    f["impact"] = {
        "annual_new_customers": annual_new, "avg_repeat_order_revenue": rep_val,
        "a1_repeat_revenue": a1["repeat_lift_pp"], "a1_per_pp": annual_new / 100 * rep_val, "a1_low": a1["repeat_lift_low_pp"], "a1_high": a1["repeat_lift_high_pp"],
        "a2_late_orders_avoided": avoided, "a2_target_late_rate_2018": t18_late,
        "a2_review_uplift": review_uplift, "a2_repeat_revenue": a2_rev,
        "a3_multi_item_share": (orders.n_items > 1).mean(), "a3_avg_addon_revenue": addon,
        "a3_basket_revenue": a3, "annual_orders": annual_orders,
        "total_revenue": total, "total_share_of_annual": total / annual_rev_2018,
    }

    facts.update("analysis", f)
    print(f"analysis: revenue R${kpi['revenue']:,.0f}, repeat {kpi['repeat_rate']:.2%}, "
          f"late review {late_s.mean():.2f} vs {on_s.mean():.2f}, impact R${total:,.0f}/yr")
    return f


if __name__ == "__main__":
    run()
