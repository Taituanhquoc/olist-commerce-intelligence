"""SQL and Python are independent implementations; their metrics must agree exactly."""
import pytest

from src.analysis import ntile, rfm_table
from src.warehouse import named_queries


def test_ntile_matches_sql_semantics():
    assert list(ntile(7, 5)) == [1, 1, 2, 2, 3, 4, 5]
    assert list(ntile(10, 5)) == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_headline_kpis_sql_equals_python(con, clean_tables):
    orders, _ = clean_tables
    sql = con.execute(named_queries()["headline_kpis"]).df().iloc[0]
    per_cust = orders.groupby("customer_unique_id").size()
    delivered = orders[orders.is_delivered]
    assert int(sql.orders) == len(orders)
    assert sql.revenue == pytest.approx(orders.revenue.sum(), abs=0.01)
    assert int(sql.customers) == per_cust.size
    assert sql.repeat_rate == pytest.approx((per_cust >= 2).mean(), abs=1e-12)
    assert sql.on_time_rate == pytest.approx(1 - delivered.is_late.astype(bool).mean(), abs=1e-12)
    assert sql.avg_review == pytest.approx(orders.review_score.mean(), abs=1e-12)
    assert sql.avg_delivery_days == pytest.approx(delivered.delivery_days.mean(), abs=1e-9)


def test_rfm_segments_sql_equals_python(con, clean_tables):
    orders, _ = clean_tables
    py = rfm_table(orders).segment.value_counts().sort_index()
    sql = con.execute("SELECT segment, COUNT(*) n FROM v_rfm GROUP BY 1").df().set_index("segment").n.sort_index()
    assert py.to_dict() == sql.to_dict()


def test_seller_and_category_concentration_agree(con, facts):
    sql = con.execute("SELECT SUM(CASE WHEN revenue_decile = 1 THEN revenue END) / SUM(revenue) FROM v_seller_pareto").fetchone()[0]
    assert sql == pytest.approx(facts["analysis"]["category"]["top10pct_sellers_share"], abs=1e-5)
    top10 = con.execute("SELECT SUM(revenue_share) FROM v_category_performance WHERE revenue_rank <= 10").fetchone()[0]
    assert top10 == pytest.approx(facts["analysis"]["category"]["top10_share"], abs=1e-5)


def test_item_and_order_revenue_reconcile(con):
    a = con.execute("SELECT SUM(price) FROM fact_order_items").fetchone()[0]
    b = con.execute("SELECT SUM(revenue) FROM fact_orders").fetchone()[0]
    assert a == pytest.approx(b, abs=0.01)


def test_monthly_view_sums_to_total(con, facts):
    total = con.execute("SELECT SUM(revenue), SUM(orders) FROM v_monthly_kpis").fetchone()
    assert total[0] == pytest.approx(facts["analysis"]["kpi"]["revenue"], abs=0.01)
    assert total[1] == facts["analysis"]["kpi"]["orders"]


def test_sanity_ranges(facts):
    k = facts["analysis"]["kpi"]
    assert 0 < k["repeat_rate"] < 0.2
    assert 0.5 < k["on_time_rate"] < 1
    assert 1 <= k["avg_review"] <= 5
    d = facts["analysis"]["delivery"]
    assert d["late_avg_review"] < d["ontime_avg_review"]
    assert d["review_gap_ci_low"] > 0


def test_yoy_consistent_with_revenue(facts):
    t = facts["analysis"]["trend"]
    assert t["yoy_revenue_growth"] == pytest.approx(t["revenue_2018_jan_aug"] / t["revenue_2017_jan_aug"] - 1, rel=1e-4)


def test_impact_recomputes(facts):
    a = facts["analysis"]
    i, s = a["impact"], a["assumptions"]
    assert i["a1_repeat_revenue"] == pytest.approx(
        i["annual_new_customers"] * s["repeat_lift_pp"] / 100 * i["avg_repeat_order_revenue"], rel=1e-4)
    assert i["a3_basket_revenue"] == pytest.approx(
        i["annual_orders"] * s["basket_lift_pp"] / 100 * i["a3_avg_addon_revenue"], rel=1e-4)
    assert i["total_revenue"] == pytest.approx(
        i["a1_repeat_revenue"] + i["a2_repeat_revenue"] + i["a3_basket_revenue"], rel=1e-4)
