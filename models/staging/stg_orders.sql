-- Staging orders from raw
select
    order_id,
    customer_id as user_id,
    amount_usd_cents as amount_cents,
    ordered_at
from cascade_shop.public.raw_orders