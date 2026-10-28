-- 02_analysis_views.sql
-- Star schema (fact_order_items + dims) plus the analysis views behind each business question.
-- Scope rule used everywhere: purchased 2017-01-01 to 2018-08-31, status not canceled/unavailable,
-- and at least one order item. The months outside the window hold under 300 orders in total and
-- distort month-on-month comparisons.

-- ---------------------------------------------------------------- dimensions
CREATE OR REPLACE TABLE dim_date AS
SELECT
    CAST(d AS DATE)                              AS date_key,
    year(d)                                      AS year,
    quarter(d)                                   AS quarter,
    month(d)                                     AS month,
    CAST(date_trunc('month', d) AS DATE)         AS month_start,
    strftime(d, '%Y-%m')                         AS year_month,
    dayofweek(d)                                 AS day_of_week,
    dayofweek(d) IN (0, 6)                       AS is_weekend
FROM range(DATE '2016-09-01', DATE '2018-11-01', INTERVAL 1 DAY) t(d);

CREATE OR REPLACE TABLE dim_geo AS
SELECT zip_prefix, state, lat, lng, n_points FROM stg_geolocation;

CREATE OR REPLACE TABLE dim_product AS
SELECT product_id, category, product_photos_qty, product_weight_g, volume_cm3 FROM stg_products;

CREATE OR REPLACE TABLE dim_seller AS
SELECT seller_id, zip_prefix, city, state FROM stg_sellers;

-- customer_id in Olist is per order; customer_unique_id is the person. The dim is at person grain,
-- carrying the location of their most recent order.
CREATE OR REPLACE TABLE dim_customer AS
WITH ranked AS (
    SELECT c.customer_unique_id, c.zip_prefix, c.city, c.state,
           ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.purchase_ts DESC) AS rn
    FROM stg_customers c
    JOIN stg_orders o USING (customer_id)
)
SELECT customer_unique_id, zip_prefix, city, state FROM ranked WHERE rn = 1;

-- ---------------------------------------------------------------- facts
CREATE OR REPLACE TABLE fact_order_items AS
SELECT
    i.order_id,
    i.order_item_id,
    c.customer_unique_id,
    i.product_id,
    i.seller_id,
    o.purchase_date                         AS date_key,
    o.purchase_month,
    i.category,
    c.state                                 AS customer_state,
    i.price,
    i.freight_value
FROM stg_order_items i
JOIN stg_orders o    USING (order_id)
JOIN stg_customers c USING (customer_id)
WHERE o.in_window AND o.is_revenue_status;

-- Order grain fact used by most analyses. revenue = item prices (freight reported separately).
CREATE OR REPLACE TABLE fact_orders AS
WITH items AS (
    SELECT order_id,
           COUNT(*)            AS n_items,
           SUM(price)          AS revenue,
           SUM(freight_value)  AS freight,
           COUNT(DISTINCT seller_id) AS n_sellers
    FROM stg_order_items GROUP BY order_id
),
primary_cat AS (   -- category of the highest-priced item; ties go to the first item
    SELECT order_id, category AS primary_category
    FROM (SELECT order_id, category,
                 ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY price DESC, order_item_id) AS rn
          FROM stg_order_items) WHERE rn = 1
),
base AS (
    SELECT
        o.order_id, c.customer_unique_id, o.purchase_ts, o.purchase_date, o.purchase_month,
        o.order_status, c.state AS customer_state,
        it.n_items, it.revenue, it.freight, it.n_sellers, pc.primary_category,
        p.payment_total, p.primary_payment_type, p.max_installments,
        o.is_delivered, o.delivery_days, o.delay_days,
        CASE WHEN o.is_delivered THEN o.delay_days > 0 END AS is_late,
        r.review_score
    FROM stg_orders o
    JOIN stg_customers c   USING (customer_id)
    JOIN items it          USING (order_id)
    JOIN primary_cat pc    USING (order_id)
    LEFT JOIN stg_payments p USING (order_id)
    LEFT JOIN stg_reviews r  USING (order_id)
    WHERE o.in_window AND o.is_revenue_status
)
SELECT *,
       ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchase_ts, order_id) AS customer_order_seq
FROM base;

CREATE INDEX IF NOT EXISTS ix_fact_orders_customer ON fact_orders (customer_unique_id);

-- ---------------------------------------------------------------- Q1 trend
-- Q: How are revenue, orders and AOV moving month on month and year on year?
-- Logic: monthly aggregate, LAG for MoM and YoY, running SUM for cumulative revenue.
-- Output: one row per month.
CREATE OR REPLACE VIEW v_monthly_kpis AS
WITH m AS (
    SELECT purchase_month AS month,
           SUM(revenue)                                    AS revenue,
           COUNT(*)                                        AS orders,
           COUNT(DISTINCT customer_unique_id)              AS customers,
           SUM(CASE WHEN customer_order_seq = 1 THEN 1 ELSE 0 END) AS new_customers,
           SUM(freight)                                    AS freight
    FROM fact_orders GROUP BY 1
)
SELECT month, revenue, orders, revenue / orders AS aov, customers, new_customers, freight,
       revenue / LAG(revenue)     OVER (ORDER BY month) - 1          AS mom_growth,
       revenue / LAG(revenue, 12) OVER (ORDER BY month) - 1          AS yoy_growth,
       SUM(revenue) OVER (ORDER BY month ROWS UNBOUNDED PRECEDING)   AS running_revenue
FROM m;

-- ---------------------------------------------------------------- Q2 categories and sellers
-- Q: Which categories carry revenue, and how long is the tail?
-- Logic: item-level revenue by category, rank, share and cumulative share (Pareto).
CREATE OR REPLACE VIEW v_category_performance AS
WITH c AS (
    SELECT category, SUM(price) AS revenue, COUNT(*) AS items, COUNT(DISTINCT order_id) AS orders,
           SUM(freight_value) / SUM(price) AS freight_ratio
    FROM fact_order_items GROUP BY 1
)
SELECT category, revenue, items, orders, freight_ratio,
       revenue / SUM(revenue) OVER ()                                                AS revenue_share,
       RANK() OVER (ORDER BY revenue DESC)                                           AS revenue_rank,
       SUM(revenue) OVER (ORDER BY revenue DESC ROWS UNBOUNDED PRECEDING)
           / SUM(revenue) OVER ()                                                    AS cumulative_share
FROM c;

-- Q: Who are the top three sellers inside each of the top categories?
-- Logic: ROW_NUMBER per category ordered by seller revenue.
CREATE OR REPLACE VIEW v_top_sellers_per_category AS
WITH s AS (
    SELECT category, seller_id, SUM(price) AS revenue, COUNT(DISTINCT order_id) AS orders
    FROM fact_order_items GROUP BY 1, 2
)
SELECT * FROM (
    SELECT s.*, ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC, seller_id) AS rank_in_category
    FROM s
) WHERE rank_in_category <= 3;

-- Q: How concentrated is revenue across sellers?
-- Logic: seller revenue ranked, NTILE(10) deciles and cumulative share.
CREATE OR REPLACE VIEW v_seller_pareto AS
WITH s AS (SELECT seller_id, SUM(price) AS revenue FROM fact_order_items GROUP BY 1)
SELECT seller_id, revenue,
       ROW_NUMBER() OVER (ORDER BY revenue DESC, seller_id)                       AS seller_rank,
       NTILE(10)    OVER (ORDER BY revenue DESC, seller_id)                       AS revenue_decile,
       SUM(revenue) OVER (ORDER BY revenue DESC, seller_id ROWS UNBOUNDED PRECEDING)
           / SUM(revenue) OVER ()                                                 AS cumulative_share
FROM s;

-- ---------------------------------------------------------------- Q3 RFM
-- Q: Which customer segments exist and what are they worth?
-- Logic: snapshot = day after the window. R and M scored with NTILE(5); F is scored from the order
--        count because 97% of customers have exactly one order, which makes an F quintile meaningless.
CREATE OR REPLACE VIEW v_rfm AS
WITH c AS (
    SELECT customer_unique_id,
           date_diff('day', MAX(purchase_date), DATE '2018-09-01') AS recency_days,
           COUNT(*)                                                AS frequency,
           SUM(revenue)                                            AS monetary
    FROM fact_orders GROUP BY 1
),
scored AS (
    SELECT c.*,
           NTILE(5) OVER (ORDER BY recency_days DESC, customer_unique_id) AS r_score,
           CASE WHEN frequency = 1 THEN 1 WHEN frequency = 2 THEN 4 ELSE 5 END AS f_score,
           NTILE(5) OVER (ORDER BY monetary ASC, customer_unique_id)      AS m_score
    FROM c
)
SELECT *,
       CASE
           WHEN frequency >= 2 AND r_score >= 4 THEN 'Champions'
           WHEN frequency >= 2                  THEN 'Loyal'
           WHEN r_score >= 4 AND m_score >= 4   THEN 'Promising'
           WHEN r_score >= 4                    THEN 'New Customers'
           WHEN r_score >= 2 AND m_score >= 4   THEN 'At-Risk'
           WHEN r_score >= 2                    THEN 'Hibernating'
           ELSE 'Lost'
       END AS segment
FROM scored;

CREATE OR REPLACE VIEW v_rfm_segments AS
SELECT segment,
       COUNT(*)                                   AS customers,
       COUNT(*) / SUM(COUNT(*)) OVER ()           AS customer_share,
       SUM(monetary)                              AS revenue,
       SUM(monetary) / SUM(SUM(monetary)) OVER () AS revenue_share,
       AVG(monetary)                              AS avg_revenue,
       AVG(recency_days)                          AS avg_recency_days,
       AVG(frequency)                             AS avg_frequency
FROM v_rfm GROUP BY 1;

-- ---------------------------------------------------------------- Q4 cohorts
-- Q: Do customers come back after their first purchase?
-- Logic: cohort = month of first order; activity = distinct customers ordering k months later.
CREATE OR REPLACE VIEW v_cohort_retention AS
WITH firsts AS (
    SELECT customer_unique_id, MIN(purchase_month) AS cohort_month FROM fact_orders GROUP BY 1
),
activity AS (
    SELECT DISTINCT f.customer_unique_id, f.cohort_month,
           date_diff('month', f.cohort_month, o.purchase_month) AS months_since_first
    FROM firsts f JOIN fact_orders o USING (customer_unique_id)
),
sizes AS (SELECT cohort_month, COUNT(*) AS cohort_size FROM firsts GROUP BY 1)
SELECT a.cohort_month, a.months_since_first, s.cohort_size,
       COUNT(*)                  AS active_customers,
       COUNT(*) / s.cohort_size  AS retention_rate
FROM activity a JOIN sizes s USING (cohort_month)
GROUP BY a.cohort_month, a.months_since_first, s.cohort_size;

-- ---------------------------------------------------------------- Q5 delivery vs reviews
-- Q: How much does a late delivery cost in review score?
-- Logic: delivered orders bucketed by days early/late against the promised date.
CREATE OR REPLACE VIEW v_delivery_review AS
SELECT
    CASE
        WHEN delay_days <= -15 THEN '1. 15+ days early'
        WHEN delay_days <= -8  THEN '2. 8-14 days early'
        WHEN delay_days <= -1  THEN '3. 1-7 days early'
        WHEN delay_days = 0    THEN '4. On the promised day'
        WHEN delay_days <= 3   THEN '5. 1-3 days late'
        WHEN delay_days <= 7   THEN '6. 4-7 days late'
        ELSE                        '7. 8+ days late'
    END                                                    AS delay_bucket,
    COUNT(*)                                               AS orders,
    AVG(review_score)                                      AS avg_review,
    AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END)   AS low_review_share
FROM fact_orders
WHERE is_delivered AND review_score IS NOT NULL
GROUP BY 1;

-- ---------------------------------------------------------------- Q6 logistics by state
-- Q: Which customer states have the worst delivery experience?
CREATE OR REPLACE VIEW v_state_logistics AS
SELECT customer_state,
       COUNT(*)                                          AS delivered_orders,
       AVG(delivery_days)                                AS avg_delivery_days,
       AVG(CASE WHEN is_late THEN 1.0 ELSE 0 END)        AS late_rate,
       SUM(CASE WHEN is_late THEN 1 ELSE 0 END)          AS late_orders,
       AVG(review_score)                                 AS avg_review,
       SUM(revenue)                                      AS revenue
FROM fact_orders
WHERE is_delivered
GROUP BY 1;

-- ---------------------------------------------------------------- Q7 payments
-- Q: Does payment method relate to order value?
CREATE OR REPLACE VIEW v_payment_mix AS
SELECT COALESCE(primary_payment_type, 'unknown')   AS payment_type,
       COUNT(*)                                     AS orders,
       COUNT(*) / SUM(COUNT(*)) OVER ()             AS order_share,
       SUM(revenue) / COUNT(*)                      AS aov,
       AVG(max_installments)                        AS avg_installments
FROM fact_orders GROUP BY 1;

CREATE OR REPLACE VIEW v_installments_aov AS
SELECT CASE WHEN max_installments <= 1 THEN '1 (single payment)'
            WHEN max_installments <= 3 THEN '2-3'
            WHEN max_installments <= 6 THEN '4-6'
            ELSE '7+' END                 AS installment_band,
       COUNT(*)                            AS orders,
       SUM(revenue) / COUNT(*)             AS aov
FROM fact_orders
WHERE primary_payment_type = 'credit_card'
GROUP BY 1;
