"""Exploratory charts. Each title states the finding; each figure carries a one-line takeaway."""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import numpy as np

from src import facts
from src.clean import load
from src.plotstyle import INK_2, SERIES, brl, save


def run() -> dict:
    orders, items = load()
    out: dict = {"figures": []}

    # 1. monthly revenue
    m = orders.groupby("purchase_month").agg(revenue=("revenue", "sum"), orders=("order_id", "size"),
                                             new=("customer_order_seq", lambda s: (s == 1).sum()))
    r18 = m.loc["2018"]
    jan_apr, may_aug = r18.revenue.iloc[:4].mean(), r18.revenue.iloc[4:].mean()
    out.update(avg_monthly_revenue_2018_jan_apr=jan_apr, avg_monthly_revenue_2018_may_aug=may_aug,
               run_rate_change_2018=may_aug / jan_apr - 1,
               peak_month=m.revenue.idxmax().strftime("%Y-%m"), peak_month_revenue=m.revenue.max(),
               revenue_jan_2017=m.revenue.iloc[0], avg_new_customers_2018=r18.new.mean(),
               avg_new_customers_2017_h2=m.loc["2017-07":"2017-12"].new.mean())
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(m.index, m.revenue / 1e6, color=SERIES[0], marker="o", markersize=4)
    ax.axvspan(m.index[12], m.index[-1], color="#f0efec", zorder=0)
    ax.annotate(f"Nov 2017 peak {brl(m.revenue.max())}", (m.revenue.idxmax(), m.revenue.max() / 1e6),
                xytext=(-120, 4), textcoords="offset points", fontsize=9, color=INK_2)
    ax.set_title(f"Revenue ramped through 2017, then stalled in 2018: {brl(may_aug)}/month in May-Aug "
                 f"vs {brl(jan_apr)} in Jan-Apr", fontsize=11)
    ax.set_ylabel("Revenue (R$ millions)")
    ax.yaxis.set_major_formatter(mt.FormatStrFormatter("%.1f"))
    out["figures"].append(save(fig, "01_monthly_revenue",
                               "Takeaway: the 2018 run-rate is flat to down, so YoY growth flatters the current trajectory."))

    # 2. new customers
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.bar(m.index, m.new, width=20, color=SERIES[0])
    ax.set_title(f"New customers plateaued at about {r18.new.mean():,.0f} a month in 2018", fontsize=11)
    ax.set_ylabel("First-time customers")
    ax.yaxis.set_major_formatter(mt.StrMethodFormatter("{x:,.0f}"))
    out["figures"].append(save(fig, "02_new_customers",
                               "Takeaway: acquisition stopped growing, and almost no one comes back, so revenue flattened."))

    # 3. delivery time distribution
    d = orders[orders.is_delivered]
    med = d.delivery_days.median()
    out.update(median_delivery_days=med, p90_delivery_days=d.delivery_days.quantile(0.9))
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.hist(d.delivery_days.clip(upper=60), bins=60, color=SERIES[0], edgecolor="#fcfcfb", linewidth=0.5)
    ax.axvline(med, color=INK_2, linewidth=1)
    ax.text(med + 0.5, ax.get_ylim()[1] * 0.9, f"median {med:.1f} days", fontsize=9, color=INK_2)
    ax.set_title(f"Half of orders arrive within {med:.0f} days; one in ten takes over "
                 f"{d.delivery_days.quantile(0.9):.0f}", fontsize=11)
    ax.set_xlabel("Days from purchase to delivery (capped at 60)")
    ax.set_ylabel("Delivered orders")
    out["figures"].append(save(fig, "03_delivery_days", "Takeaway: a long right tail of slow deliveries drives the late-order problem."))

    # 4. review score distribution
    rv = orders.review_score.value_counts(normalize=True).sort_index()
    out.update(review_5_share=rv.get(5, 0), review_1_share=rv.get(1, 0))
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(rv.index.astype(int).astype(str), rv.values * 100, color=SERIES[0], width=0.6)
    ax.set_title(f"{rv.get(5, 0):.0%} of reviews are 5 stars, but {rv.get(1, 0):.0%} are 1 star", fontsize=11)
    ax.set_xlabel("Review score")
    ax.set_ylabel("Share of reviewed orders (%)")
    out["figures"].append(save(fig, "04_review_scores", "Takeaway: reviews are polarised; the 1-star tail is what to explain."))

    # 5. top categories
    cat = items.groupby("category").price.sum().sort_values(ascending=False)
    top = cat.head(15)[::-1]
    out.update(top_category=cat.index[0], top_category_share=cat.iloc[0] / cat.sum())
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top.index.str.replace("_", " "), top.values / 1e6, color=SERIES[0], height=0.65)
    ax.set_title(f"The top 10 of {len(cat)} categories carry {cat.head(10).sum() / cat.sum():.0%} of revenue", fontsize=11)
    ax.set_xlabel("Revenue (R$ millions)")
    ax.grid(axis="y", visible=False)
    out["figures"].append(save(fig, "05_top_categories", "Takeaway: growth plans should start with a handful of categories."))

    # 6. order value distribution
    out.update(median_order_value=orders.revenue.median())
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.hist(np.log10(orders.revenue), bins=60, color=SERIES[0], edgecolor="#fcfcfb", linewidth=0.5)
    ax.set_xticks([1, 1.5, 2, 2.5, 3, 3.5], ["R$10", "R$32", "R$100", "R$316", "R$1,000", "R$3,162"])
    ax.set_title(f"Typical order is small: median {brl(orders.revenue.median())}, mean {brl(orders.revenue.mean())}", fontsize=11)
    ax.set_xlabel("Order revenue (log scale)")
    ax.set_ylabel("Orders")
    out["figures"].append(save(fig, "06_order_value", "Takeaway: the mean is pulled up by a long tail of high-ticket orders."))

    facts.update("eda", out)
    print(f"eda: {len(out['figures'])} figures")
    return out


if __name__ == "__main__":
    run()
