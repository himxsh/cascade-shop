-- cascade-shop warehouse schema (idempotent-ish for fresh volume)

CREATE TABLE IF NOT EXISTS raw_orders (
    order_id    BIGINT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stg_orders (
    order_id    BIGINT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fct_orders (
    order_id    BIGINT PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    ordered_at  TIMESTAMPTZ NOT NULL
);

TRUNCATE raw_orders, stg_orders, fct_orders;

INSERT INTO raw_orders (order_id, user_id, amount_cents, ordered_at) VALUES
    (1, 101, 2500, '2026-01-02T10:00:00Z'),
    (2, 102, 1800, '2026-01-03T11:00:00Z'),
    (3, 101, 4200, '2026-01-04T12:00:00Z');

INSERT INTO stg_orders (order_id, user_id, amount_cents, ordered_at)
SELECT order_id, user_id, amount_cents, ordered_at FROM raw_orders;

INSERT INTO fct_orders (order_id, user_id, amount_cents, ordered_at)
SELECT order_id, user_id, amount_cents, ordered_at FROM stg_orders;
