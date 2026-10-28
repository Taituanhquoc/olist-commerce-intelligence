"""Data-quality checks on the star schema and the cleaned tables."""


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_order_grain_unique(con):
    assert scalar(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM fact_orders") == 0


def test_item_grain_unique(con):
    assert scalar(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id || '-' || order_item_id) FROM fact_order_items") == 0


def test_every_item_has_an_order(con):
    assert scalar(con, "SELECT COUNT(*) FROM fact_order_items i LEFT JOIN fact_orders o USING (order_id) "
                       "WHERE o.order_id IS NULL") == 0


def test_prices_positive(con):
    assert scalar(con, "SELECT COUNT(*) FROM fact_order_items WHERE price <= 0 OR freight_value < 0") == 0


def test_window_and_status_scope(con):
    assert scalar(con, "SELECT COUNT(*) FROM fact_orders WHERE purchase_ts < TIMESTAMP '2017-01-01' "
                       "OR purchase_ts >= TIMESTAMP '2018-09-01'") == 0
    assert scalar(con, "SELECT COUNT(*) FROM fact_orders WHERE order_status IN ('canceled', 'unavailable')") == 0


def test_review_scores_valid(con):
    assert scalar(con, "SELECT COUNT(*) FROM fact_orders WHERE review_score NOT BETWEEN 1 AND 5") == 0


def test_customer_order_sequence_contiguous(con):
    bad = scalar(con, "SELECT COUNT(*) FROM (SELECT customer_unique_id, MAX(customer_order_seq) m, COUNT(*) n "
                      "FROM fact_orders GROUP BY 1) WHERE m <> n")
    assert bad == 0


def test_delivery_fields_consistent(clean_tables):
    orders, _ = clean_tables
    delivered = orders[orders.is_delivered]
    assert delivered.delivery_days.notna().all()
    assert (delivered.delivery_days >= 0).all()
    assert orders[~orders.is_delivered].is_late.isna().all()


def test_one_review_per_order(con):
    assert scalar(con, "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM stg_reviews") == 0
