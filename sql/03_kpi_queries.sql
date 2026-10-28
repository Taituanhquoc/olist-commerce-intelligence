-- 03_kpi_queries.sql
-- Named queries run by src/warehouse.py; each result is saved to reports/sql_outputs/<name>.csv
-- and the headline values are cross-checked against the Python pipeline in tests/.

-- name: headline_kpis
-- Q: What are the headline numbers for the analysis window?
-- Logic: order-grain fact; repeat rate = customers with 2+ orders / all customers.
-- Output: one row.
SELECT
    SUM(revenue)                                                        AS revenue,
    COUNT(*)                                                            AS orders,
    COUNT(DISTINCT customer_unique_id)                                  AS customers,
    SUM(revenue) / COUNT(*)                                             AS aov,
    SUM(freight)                                                        AS freight,
    AVG(n_items)                                                        AS items_per_order,
    (SELECT AVG(CASE WHEN n >= 2 THEN 1.0 ELSE 0 END)
       FROM (SELECT COUNT(*) AS n FROM fact_orders GROUP BY customer_unique_id)) AS repeat_rate,
    AVG(CASE WHEN is_delivered THEN CASE WHEN is_late THEN 0.0 ELSE 1.0 END END) AS on_time_rate,
    AVG(CASE WHEN is_delivered THEN delivery_days END)                  AS avg_delivery_days,
    AVG(review_score)                                                   AS avg_review
FROM fact_orders;

-- name: yoy_jan_aug
-- Q: How does Jan-Aug 2018 compare with Jan-Aug 2017?
-- Logic: same eight calendar months each year, so seasonality cancels out.
-- Output: one row per year.
SELECT year(purchase_month) AS year,
       SUM(revenue)         AS revenue,
       COUNT(*)             AS orders,
       SUM(revenue) / COUNT(*) AS aov
FROM fact_orders
WHERE month(purchase_month) <= 8
GROUP BY 1 ORDER BY 1;

-- name: monthly_kpis
-- Q: Month-by-month trend with MoM / YoY growth and running revenue.
SELECT * FROM v_monthly_kpis ORDER BY month;

-- name: category_top15
-- Q: Top 15 categories by revenue with share and cumulative share.
SELECT * FROM v_category_performance WHERE revenue_rank <= 15 ORDER BY revenue_rank;

-- name: category_tail
-- Q: How much revenue sits in the bottom half of categories?
-- Logic: rank categories; bottom half = rank above the median rank.
SELECT COUNT(*)                                        AS categories,
       SUM(CASE WHEN revenue_rank > (SELECT COUNT(*) FROM v_category_performance) / 2
                THEN revenue_share ELSE 0 END)         AS bottom_half_share,
       SUM(CASE WHEN revenue_rank <= 10 THEN revenue_share ELSE 0 END) AS top10_share
FROM v_category_performance;

-- name: top_sellers_per_category
-- Q: Top three sellers in each of the five largest categories.
SELECT t.* FROM v_top_sellers_per_category t
JOIN v_category_performance c USING (category)
WHERE c.revenue_rank <= 5
ORDER BY c.revenue_rank, t.rank_in_category;

-- name: seller_concentration
-- Q: Share of revenue from the top 10% and top 20% of sellers.
SELECT COUNT(*)                                                      AS sellers,
       SUM(CASE WHEN revenue_decile = 1 THEN revenue END) / SUM(revenue)       AS top10pct_share,
       SUM(CASE WHEN revenue_decile <= 2 THEN revenue END) / SUM(revenue)      AS top20pct_share
FROM v_seller_pareto;

-- name: rfm_segments
-- Q: Size and value of each RFM segment.
SELECT * FROM v_rfm_segments ORDER BY revenue DESC;

-- name: cohort_retention
-- Q: Cohort retention matrix (long format).
SELECT * FROM v_cohort_retention ORDER BY cohort_month, months_since_first;

-- name: delivery_review
-- Q: Average review by delivery delay bucket.
SELECT * FROM v_delivery_review ORDER BY delay_bucket;

-- name: state_logistics
-- Q: States ranked by late-delivery rate (states with at least 300 delivered orders).
SELECT * FROM v_state_logistics WHERE delivered_orders >= 300 ORDER BY late_rate DESC;

-- name: payment_mix
-- Q: Order share, AOV and installments by primary payment type.
SELECT * FROM v_payment_mix ORDER BY orders DESC;

-- name: installments_aov
-- Q: Credit-card AOV by installment band.
SELECT * FROM v_installments_aov ORDER BY installment_band;
