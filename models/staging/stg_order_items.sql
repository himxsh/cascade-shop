-- Staging items with product sku
select
    i.order_id,
    i.product_id,
    p.sku,
    i.qty,
    i.line_amount_cents
from cascade_shop.public.raw_order_items i
join cascade_shop.public.raw_products p
  on p.product_id = i.product_id
