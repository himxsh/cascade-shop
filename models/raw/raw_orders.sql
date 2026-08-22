-- Landing: orders
-- cascade: rename user_id -> customer_id
select
    order_id,
    customer_id,
    amount_cents,
    ordered_at
from cascade_shop.public.raw_orders
