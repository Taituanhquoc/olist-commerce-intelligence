-- 00_schema.sql
-- Business question: none directly; this file lands the nine Olist CSVs in a typed raw layer.
-- Logic: one table per source file, column types declared up front so bad values fail loudly.
--        Zip prefixes stay VARCHAR so leading zeros survive. ${RAW} is replaced by src/warehouse.py.
-- Output: schema `raw` with nine tables, row counts identical to the CSVs.

CREATE SCHEMA IF NOT EXISTS raw;

CREATE OR REPLACE TABLE raw.customers (
    customer_id              VARCHAR NOT NULL,
    customer_unique_id       VARCHAR NOT NULL,
    customer_zip_code_prefix VARCHAR,
    customer_city            VARCHAR,
    customer_state           VARCHAR
);

CREATE OR REPLACE TABLE raw.geolocation (
    geolocation_zip_code_prefix VARCHAR,
    geolocation_lat             DOUBLE,
    geolocation_lng             DOUBLE,
    geolocation_city            VARCHAR,
    geolocation_state           VARCHAR
);

CREATE OR REPLACE TABLE raw.order_items (
    order_id            VARCHAR NOT NULL,
    order_item_id       INTEGER NOT NULL,
    product_id          VARCHAR,
    seller_id           VARCHAR,
    shipping_limit_date TIMESTAMP,
    price               DOUBLE,
    freight_value       DOUBLE
);

CREATE OR REPLACE TABLE raw.order_payments (
    order_id             VARCHAR NOT NULL,
    payment_sequential   INTEGER,
    payment_type         VARCHAR,
    payment_installments INTEGER,
    payment_value        DOUBLE
);

CREATE OR REPLACE TABLE raw.order_reviews (
    review_id               VARCHAR NOT NULL,
    order_id                VARCHAR NOT NULL,
    review_score            INTEGER,
    review_comment_title    VARCHAR,
    review_comment_message  VARCHAR,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE OR REPLACE TABLE raw.orders (
    order_id                      VARCHAR NOT NULL,
    customer_id                   VARCHAR NOT NULL,
    order_status                  VARCHAR,
    order_purchase_timestamp      TIMESTAMP,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE OR REPLACE TABLE raw.products (
    product_id                 VARCHAR NOT NULL,
    product_category_name      VARCHAR,
    product_name_lenght        INTEGER,   -- source spelling kept
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           DOUBLE,
    product_length_cm          DOUBLE,
    product_height_cm          DOUBLE,
    product_width_cm           DOUBLE
);

CREATE OR REPLACE TABLE raw.sellers (
    seller_id              VARCHAR NOT NULL,
    seller_zip_code_prefix VARCHAR,
    seller_city            VARCHAR,
    seller_state           VARCHAR
);

CREATE OR REPLACE TABLE raw.category_translation (
    product_category_name         VARCHAR NOT NULL,
    product_category_name_english VARCHAR NOT NULL
);

INSERT INTO raw.customers            SELECT * FROM read_csv('${RAW}/olist_customers_dataset.csv',            header = true, all_varchar = true);
INSERT INTO raw.geolocation          SELECT * FROM read_csv('${RAW}/olist_geolocation_dataset.csv',          header = true, all_varchar = true);
INSERT INTO raw.order_items          SELECT * FROM read_csv('${RAW}/olist_order_items_dataset.csv',          header = true, all_varchar = true);
INSERT INTO raw.order_payments       SELECT * FROM read_csv('${RAW}/olist_order_payments_dataset.csv',       header = true, all_varchar = true);
INSERT INTO raw.order_reviews        SELECT * FROM read_csv('${RAW}/olist_order_reviews_dataset.csv',        header = true, all_varchar = true);
INSERT INTO raw.orders               SELECT * FROM read_csv('${RAW}/olist_orders_dataset.csv',               header = true, all_varchar = true);
INSERT INTO raw.products             SELECT * FROM read_csv('${RAW}/olist_products_dataset.csv',             header = true, all_varchar = true);
INSERT INTO raw.sellers              SELECT * FROM read_csv('${RAW}/olist_sellers_dataset.csv',              header = true, all_varchar = true);
INSERT INTO raw.category_translation SELECT * FROM read_csv('${RAW}/product_category_name_translation.csv', header = true, all_varchar = true);

-- Indexes on the join keys used by the staging layer.
CREATE INDEX IF NOT EXISTS ix_raw_orders_order      ON raw.orders (order_id);
CREATE INDEX IF NOT EXISTS ix_raw_orders_customer   ON raw.orders (customer_id);
CREATE INDEX IF NOT EXISTS ix_raw_items_order       ON raw.order_items (order_id);
CREATE INDEX IF NOT EXISTS ix_raw_payments_order    ON raw.order_payments (order_id);
CREATE INDEX IF NOT EXISTS ix_raw_reviews_order     ON raw.order_reviews (order_id);
CREATE INDEX IF NOT EXISTS ix_raw_customers_id      ON raw.customers (customer_id);
