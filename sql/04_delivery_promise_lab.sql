-- DELIVERY PROMISE LAB / independent portfolio extension
-- Engine: DuckDB (run AFTER the original 00-02 SQL scripts built fact_orders)
-- Order grain. No seller-level blame is inferred from orders with multiple sellers.
-- The observed relationships in these queries do NOT identify causal treatment effects.

-- 01. Regional KPI with minimum-volume reporting rule and sample-size adjustment.
-- Use exactly the same delivered-order definition as the original fact.
CREATE OR REPLACE VIEW v_promise_state_priority AS
WITH national AS (
    SELECT AVG(CAST(is_late AS DOUBLE)) AS national_rate
    FROM fact_orders WHERE is_delivered = TRUE
), state_rollup AS (
    SELECT customer_state AS state,
           COUNT(*) AS delivered_orders,
           SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_orders,
           AVG(CAST(is_late AS DOUBLE)) AS observed_late_rate,
           AVG(review_score) AS avg_review,
           SUM(revenue) AS revenue_brl
    FROM fact_orders
    WHERE is_delivered = TRUE
    GROUP BY customer_state
    HAVING COUNT(*) >= 300
), scored AS (
    SELECT s.*,n.national_rate,
           (s.late_orders + 200.0 * n.national_rate) /
                 (s.delivered_orders + 200.0) AS adjusted_late_rate,
           GREATEST(0, s.late_orders - s.delivered_orders * n.national_rate) AS excess_late_vs_national
    FROM state_rollup s CROSS JOIN national n
)
SELECT *,
       ROW_NUMBER() OVER (ORDER BY adjusted_late_rate DESC, delivered_orders DESC, state) AS risk_rank,
       ROUND(100.0 * observed_late_rate, 2) AS observed_late_pct
FROM scored;

-- 02. High-volume opportunity vs high-percentage risk. Distinguish rates from totals.
SELECT state, delivered_orders, late_orders, observed_late_pct,
       ROUND(100 * adjusted_late_rate, 2) AS adjusted_late_pct,
       ROUND(excess_late_vs_national,1) AS excess_late_vs_national,
       risk_rank
FROM v_promise_state_priority
ORDER BY excess_late_vs_national DESC, delivered_orders DESC;

-- 03. Month-by-month state QA: detect if the risk is isolated to unusual periods.
-- DuckDB GROUP BY ALL is explicit about non-aggregated columns.
WITH monthly AS (
    SELECT customer_state AS state, purchase_month AS month,
           COUNT(*) AS delivered_orders,
           SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_orders
    FROM fact_orders WHERE is_delivered = TRUE
    GROUP BY ALL
)
SELECT state, month, delivered_orders, late_orders,
       ROUND(100.0 * late_orders / NULLIF(delivered_orders,0),2) AS late_pct,
       SUM(late_orders) OVER(PARTITION BY state ORDER BY month ROWS UNBOUNDED PRECEDING) AS running_late_orders
FROM monthly
ORDER BY month, state;

-- 04. Review score and delivery status: descriptive association only.
SELECT CASE WHEN is_late THEN 'Late' ELSE 'On time' END AS delivery_status,
       COUNT(*) AS orders_with_reviews,
       ROUND(AVG(review_score),3) AS avg_review_score,
       ROUND(100.0 * AVG(CAST(review_score <= 2 AS DOUBLE)),2) AS low_review_pct
FROM fact_orders
WHERE is_delivered = TRUE AND review_score IS NOT NULL
GROUP BY delivery_status;

-- 05. A controlled descriptive breakdown: delivery delay rates by purchase period and state.
-- A useful next step would be a regression with state, month, basket value and other controls.
WITH t AS (
   SELECT customer_state AS state, purchase_month AS month,
          SUM(CASE WHEN is_late THEN 1 ELSE 0 END) AS late_orders,
          COUNT(*) AS delivered_orders,
          AVG(revenue) AS mean_order_value
   FROM fact_orders WHERE is_delivered = TRUE GROUP BY ALL
)
SELECT t.*,
       ROUND(100.0*late_orders/NULLIF(delivered_orders,0),2) AS late_pct,
       DENSE_RANK() OVER(PARTITION BY month ORDER BY late_orders DESC) AS late_count_rank_month
FROM t
WHERE delivered_orders >= 30;

-- NB: Query-1 reporting threshold is >=300; it does NOT cover all national deliveries.
-- The dashboard explicitly shows the excluded national volume, rather than filling with zeros.
