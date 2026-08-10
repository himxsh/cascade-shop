-- Staging customers from raw
select
    customer_id,
    email_address as email,
    full_name,
    country
from cascade_shop.public.raw_customers