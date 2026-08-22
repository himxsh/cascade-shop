-- Mart: revenue by customer
select
    f.customer_id,
    c.email,
    c.country,
    count(*) as order_count,
    sum(f.amount_cents) as revenue_cents
from cascade_shop.public.fct_orders f
join cascade_shop.public.stg_customers c
  on c.customer_id = f.customer_id
group by f.customer_id, c.email, c.country
