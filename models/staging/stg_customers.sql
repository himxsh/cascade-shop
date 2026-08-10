-- Staging customers from raw
select
    customer_id,
    email_address,
    full_name,
    country
from cascade_shop.public.raw_customers
