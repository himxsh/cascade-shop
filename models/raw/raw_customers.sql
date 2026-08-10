-- Landing: customers
-- cascade: rename email -> email_address
select
    customer_id,
    email_address,
    full_name,
    country
from cascade_shop.public.raw_customers
