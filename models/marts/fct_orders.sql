-- Fact: order grain
select
    order_id,
    user_id as customer_key,
    user_id,
    amount_cents,
    ordered_at
from cascade_shop.public.int_orders_enriched