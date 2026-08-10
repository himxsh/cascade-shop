-- Landing: orders
-- cascade: rename user_id -> customer_id
-- cascade: rename amount_cents -> amount_usd_cents
select
    order_id,
    customer_id,
    amount_usd_cents,
    ordered_at
from cascade_shop.public.raw_orders
