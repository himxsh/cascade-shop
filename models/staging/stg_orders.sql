-- Staging: clean raw orders for downstream marts.
select
    order_id,
    user_id,
    amount_cents,
    ordered_at
from cascade_shop.public.raw_orders
