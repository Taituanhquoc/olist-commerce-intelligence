-- 01_staging_clean.sql
-- Business question: can the raw tables be trusted for revenue, delivery and review metrics?
-- Logic: type-clean and standardise every source, de-duplicate where the grain is violated,
--        and add flags instead of deleting rows, so every exclusion is visible downstream.
-- Output: stg_* tables, one per source, at a documented grain.

-- Orders: one row per order_id. Flags drive scope decisions in 02_analysis_views.sql.
CREATE OR REPLACE TABLE stg_orders AS
WITH ranked AS (
    SELECT o.*,
           ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_purchase_timestamp) AS rn
    FROM raw.orders o
)
SELECT
    order_id,
    customer_id,
    lower(trim(order_status))                                           AS order_status,
    order_purchase_timestamp                                            AS purchase_ts,
    CAST(order_purchase_timestamp AS DATE)                              AS purchase_date,
    CAST(date_trunc('month', order_purchase_timestamp) AS DATE)         AS purchase_month,
    order_approved_at                                                   AS approved_ts,
    order_delivered_carrier_date                                        AS carrier_ts,
    order_delivered_customer_date                                       AS delivered_ts,
    CAST(order_estimated_delivery_date AS DATE)                         AS estimated_date,
    order_purchase_timestamp >= TIMESTAMP '2017-01-01'
        AND order_purchase_timestamp <  TIMESTAMP '2018-09-01'          AS in_window,
    lower(trim(order_status)) NOT IN ('canceled', 'unavailable')        AS is_revenue_status,
    lower(trim(order_status)) = 'delivered'
        AND order_delivered_customer_date IS NOT NULL                   AS is_delivered,
    -- delivery time in days, measured purchase -> customer receipt
    CASE WHEN order_delivered_customer_date IS NOT NULL
         THEN date_diff('second', order_purchase_timestamp, order_delivered_customer_date) / 86400.0 END
                                                                        AS delivery_days,
    -- positive = days after the promised date; compared at day grain because the promise is a date
    CASE WHEN order_delivered_customer_date IS NOT NULL
         THEN date_diff('day', CAST(order_estimated_delivery_date AS DATE), CAST(order_delivered_customer_date AS DATE)) END
                                                                        AS delay_days,
    order_delivered_carrier_date < order_purchase_timestamp             AS carrier_before_purchase
FROM ranked
WHERE rn = 1;

-- Order items: one row per (order_id, order_item_id). English category with two manual
-- translations the source file is missing, and 'unknown' where the product has no category.
CREATE OR REPLACE TABLE stg_order_items AS
SELECT
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    i.shipping_limit_date,
    i.price,
    i.freight_value,
    COALESCE(t.product_category_name_english,
             CASE p.product_category_name
                  WHEN 'pc_gamer' THEN 'pc_gamer'
                  WHEN 'portateis_cozinha_e_preparadores_de_alimentos' THEN 'small_kitchen_appliances'
             END,
             'unknown')                                                 AS category
FROM raw.order_items i
LEFT JOIN raw.products p             ON p.product_id = i.product_id
LEFT JOIN raw.category_translation t ON t.product_category_name = p.product_category_name;

-- Reviews: the source has several reviews for some orders. Keep the latest answered one.
CREATE OR REPLACE TABLE stg_reviews AS
WITH ranked AS (
    SELECT r.*,
           ROW_NUMBER() OVER (PARTITION BY order_id
                              ORDER BY review_answer_timestamp DESC NULLS LAST,
                                       review_creation_date DESC NULLS LAST,
                                       review_id) AS rn
    FROM raw.order_reviews r
)
SELECT order_id, review_id, review_score, review_creation_date, review_answer_timestamp
FROM ranked
WHERE rn = 1 AND review_score BETWEEN 1 AND 5;

-- Payments rolled up to one row per order. Primary type = the method that paid the most.
CREATE OR REPLACE TABLE stg_payments AS
WITH ranked AS (
    SELECT p.*,
           ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC, payment_sequential) AS rn
    FROM raw.order_payments p
)
SELECT
    order_id,
    SUM(payment_value)                                        AS payment_total,
    MAX(CASE WHEN rn = 1 THEN payment_type END)               AS primary_payment_type,
    MAX(payment_installments)                                 AS max_installments,
    COUNT(DISTINCT payment_type)                              AS n_payment_types
FROM ranked
GROUP BY order_id;

CREATE OR REPLACE TABLE stg_customers AS
SELECT
    customer_id,
    customer_unique_id,
    lpad(trim(customer_zip_code_prefix), 5, '0') AS zip_prefix,
    lower(trim(customer_city))                   AS city,
    upper(trim(customer_state))                  AS state
FROM raw.customers;

CREATE OR REPLACE TABLE stg_sellers AS
SELECT
    seller_id,
    lpad(trim(seller_zip_code_prefix), 5, '0') AS zip_prefix,
    lower(trim(seller_city))                   AS city,
    upper(trim(seller_state))                  AS state
FROM raw.sellers;

CREATE OR REPLACE TABLE stg_products AS
SELECT
    p.product_id,
    COALESCE(t.product_category_name_english,
             CASE p.product_category_name
                  WHEN 'pc_gamer' THEN 'pc_gamer'
                  WHEN 'portateis_cozinha_e_preparadores_de_alimentos' THEN 'small_kitchen_appliances'
             END,
             'unknown')            AS category,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm * p.product_height_cm * p.product_width_cm AS volume_cm3
FROM raw.products p
LEFT JOIN raw.category_translation t ON t.product_category_name = p.product_category_name;

-- Geolocation: ~1M rows with many points per zip prefix and some coordinates outside Brazil.
-- Keep points inside Brazil's bounding box, then take the median point per prefix.
CREATE OR REPLACE TABLE stg_geolocation AS
SELECT
    lpad(trim(geolocation_zip_code_prefix), 5, '0') AS zip_prefix,
    median(geolocation_lat)                         AS lat,
    median(geolocation_lng)                         AS lng,
    mode(upper(trim(geolocation_state)))            AS state,
    COUNT(*)                                        AS n_points
FROM raw.geolocation
WHERE geolocation_lat BETWEEN -33.75 AND 5.27
  AND geolocation_lng BETWEEN -73.99 AND -34.79
GROUP BY 1;

CREATE INDEX IF NOT EXISTS ix_stg_orders_order  ON stg_orders (order_id);
CREATE INDEX IF NOT EXISTS ix_stg_items_order   ON stg_order_items (order_id);
CREATE INDEX IF NOT EXISTS ix_stg_reviews_order ON stg_reviews (order_id);
CREATE INDEX IF NOT EXISTS ix_stg_pay_order     ON stg_payments (order_id);
CREATE INDEX IF NOT EXISTS ix_stg_cust_id       ON stg_customers (customer_id);
