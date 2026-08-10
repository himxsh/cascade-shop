-- Mart: revenue by customer
select
    f.user_id,
    c.email_address,
    c.country,
    count(*) as order_count,
    sum(f.amount_cents) as revenue_cents
from cascade_shop.public.fct_orders f
join cascade_shop.public.stg_customers c
  on c.customer_id = f.user_id
group by f.user_id, c.email_address, c.country
