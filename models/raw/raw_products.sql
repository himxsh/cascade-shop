-- Landing: products
select
    product_id,
    sku,
    product_name,
    unit_price_cents
from cascade_shop.public.raw_products
