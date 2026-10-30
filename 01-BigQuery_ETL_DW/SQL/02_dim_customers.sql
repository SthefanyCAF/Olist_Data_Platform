CREATE OR REPLACE TABLE `olist-data-platform-65749.dw_olist.dim_customers` AS
SELECT
  c.customer_id,
  c.customer_unique_id,
  c.customer_zip_code_prefix AS zip_code_prefix,
  c.customer_city            AS city,
  c.customer_state           AS state,
  CASE
    WHEN c.customer_state IN ('AC','AP','AM','PA','RO','RR','TO') THEN 'Norte'
    WHEN c.customer_state IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'Nordeste'
    WHEN c.customer_state IN ('DF','GO','MT','MS') THEN 'Centro-Oeste'
    WHEN c.customer_state IN ('ES','MG','RJ','SP') THEN 'Sudeste'
    WHEN c.customer_state IN ('PR','RS','SC') THEN 'Sul'
    ELSE 'Não informado'
  END AS region,
  g.geolocation_lat AS latitude,
  g.geolocation_lng AS longitude
FROM `olist-data-platform-65749.clean_olist.customers` AS c
LEFT JOIN `olist-data-platform-65749.clean_olist.geolocation` AS g
  ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix;