-- cascade-shop warehouse schema (fresh volume / init)

CREATE TABLE IF NOT EXISTS raw_customers (
    customer_id   BIGINT PRIMARY KEY,
    email         TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    country       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_products (
    product_id        BIGINT PRIMARY KEY,
    sku               TEXT NOT NULL,
    product_name      TEXT NOT NULL,
    unit_price_cents  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_orders (
    order_id     BIGINT PRIMARY KEY,
    user_id      BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_order_items (
    order_id          BIGINT NOT NULL,
    product_id        BIGINT NOT NULL,
    qty               INTEGER NOT NULL,
    line_amount_cents INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS stg_customers (
    customer_id BIGINT PRIMARY KEY,
    email       TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    country     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stg_products (
    product_id       BIGINT PRIMARY KEY,
    sku              TEXT NOT NULL,
    product_name     TEXT NOT NULL,
    unit_price_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS stg_orders (
    order_id     BIGINT PRIMARY KEY,
    user_id      BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at   TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS stg_order_items (
    order_id          BIGINT NOT NULL,
    product_id        BIGINT NOT NULL,
    sku               TEXT NOT NULL,
    qty               INTEGER NOT NULL,
    line_amount_cents INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS int_orders_enriched (
    order_id     BIGINT PRIMARY KEY,
    user_id      BIGINT NOT NULL,
    email        TEXT NOT NULL,
    country      TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at   TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fct_orders (
    order_id     BIGINT PRIMARY KEY,
    user_id      BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at   TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fct_order_items (
    order_id          BIGINT NOT NULL,
    product_id        BIGINT NOT NULL,
    user_id           BIGINT NOT NULL,
    qty               INTEGER NOT NULL,
    line_amount_cents INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS mart_customer_revenue (
    user_id         BIGINT PRIMARY KEY,
    email           TEXT NOT NULL,
    country         TEXT NOT NULL,
    order_count     INTEGER NOT NULL,
    revenue_cents   BIGINT NOT NULL
);

TRUNCATE
    mart_customer_revenue,
    fct_order_items,
    fct_orders,
    int_orders_enriched,
    stg_order_items,
    stg_orders,
    stg_products,
    stg_customers,
    raw_order_items,
    raw_orders,
    raw_products,
    raw_customers
CASCADE;

INSERT INTO raw_customers (customer_id, email, full_name, country) VALUES
    (101, 'alice@example.com', 'Alice Nguyen', 'US'),
    (102, 'bob@example.com', 'Bob Singh', 'IN'),
    (103, 'cara@example.com', 'Cara Mendes', 'BR'),
    (104, 'dan@example.com', 'Dan Okoye', 'NG'),
    (105, 'eva@example.com', 'Eva Klein', 'DE');

INSERT INTO raw_products (product_id, sku, product_name, unit_price_cents) VALUES
    (1, 'SKU-TEE', 'Cascade Tee', 2500),
    (2, 'SKU-HAT', 'Cascade Hat', 1800),
    (3, 'SKU-BAG', 'Cascade Bag', 4200),
    (4, 'SKU-MUG', 'Cascade Mug', 1200);

INSERT INTO raw_orders (order_id, user_id, amount_cents, ordered_at) VALUES
    (1, 101, 4300, '2026-01-02T10:00:00Z'),
    (2, 102, 1800, '2026-01-03T11:00:00Z'),
    (3, 101, 5400, '2026-01-04T12:00:00Z'),
    (4, 103, 2500, '2026-01-05T09:00:00Z'),
    (5, 104, 7000, '2026-01-06T15:00:00Z'),
    (6, 105, 1200, '2026-01-07T08:00:00Z'),
    (7, 102, 4200, '2026-01-08T14:00:00Z'),
    (8, 101, 3000, '2026-01-09T16:00:00Z');

INSERT INTO raw_order_items (order_id, product_id, qty, line_amount_cents) VALUES
    (1, 1, 1, 2500),
    (1, 2, 1, 1800),
    (2, 2, 1, 1800),
    (3, 3, 1, 4200),
    (3, 4, 1, 1200),
    (4, 1, 1, 2500),
    (5, 3, 1, 4200),
    (5, 1, 1, 2500),
    (5, 2, 1, 1800),
    (6, 4, 1, 1200),
    (7, 3, 1, 4200),
    (8, 1, 1, 2500),
    (8, 4, 1, 500);

INSERT INTO stg_customers SELECT * FROM raw_customers;
INSERT INTO stg_products SELECT * FROM raw_products;
INSERT INTO stg_orders SELECT * FROM raw_orders;

INSERT INTO stg_order_items (order_id, product_id, sku, qty, line_amount_cents)
SELECT i.order_id, i.product_id, p.sku, i.qty, i.line_amount_cents
FROM raw_order_items i
JOIN raw_products p ON p.product_id = i.product_id;

INSERT INTO int_orders_enriched (order_id, user_id, email, country, amount_cents, ordered_at)
SELECT o.order_id, o.user_id, c.email, c.country, o.amount_cents, o.ordered_at
FROM stg_orders o
JOIN stg_customers c ON c.customer_id = o.user_id;

INSERT INTO fct_orders (order_id, user_id, amount_cents, ordered_at)
SELECT order_id, user_id, amount_cents, ordered_at FROM int_orders_enriched;

INSERT INTO fct_order_items (order_id, product_id, user_id, qty, line_amount_cents)
SELECT i.order_id, i.product_id, o.user_id, i.qty, i.line_amount_cents
FROM stg_order_items i
JOIN stg_orders o ON o.order_id = i.order_id;

INSERT INTO mart_customer_revenue (user_id, email, country, order_count, revenue_cents)
SELECT
    f.user_id,
    c.email,
    c.country,
    COUNT(*)::INTEGER,
    SUM(f.amount_cents)::BIGINT
FROM fct_orders f
JOIN stg_customers c ON c.customer_id = f.user_id
GROUP BY f.user_id, c.email, c.country;
