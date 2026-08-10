-- Fact: order grain for analytics.
select
    order_id,
    user_id as customer_key,
    user_id,
    amount_cents,
    ordered_at
from cascade_shop.public.stg_orders
