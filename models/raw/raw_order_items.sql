-- Landing: order line items
select
    order_id,
    product_id,
    qty,
    line_amount_cents
from cascade_shop.public.raw_order_items
