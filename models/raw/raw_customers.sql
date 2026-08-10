-- Landing: customers
select
    customer_id,
    email,
    full_name,
    country
from cascade_shop.public.raw_customers
