-- Orders enriched with customer attributes
select
    o.order_id,
    o.user_id,
    c.email_address,
    c.country,
    o.amount_cents,
    o.ordered_at
from cascade_shop.public.stg_orders o
join cascade_shop.public.stg_customers c
  on c.customer_id = o.user_id
