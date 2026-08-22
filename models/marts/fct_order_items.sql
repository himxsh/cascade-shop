-- Fact: order item grain with purchaser
select
    i.order_id,
    i.product_id,
    o.customer_id,
    i.qty,
    i.line_amount_cents
from cascade_shop.public.stg_order_items i
join cascade_shop.public.stg_orders o
  on o.order_id = i.order_id
