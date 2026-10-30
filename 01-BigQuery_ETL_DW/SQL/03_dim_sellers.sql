CREATE OR REPLACE TABLE `olist-data-platform-65749.dw_olist.dim_sellers` AS
SELECT
  s.seller_id,
  s.seller_zip_code_prefix AS zip_code_prefix,
  s.seller_city            AS city,
  s.seller_state           AS state,
  CASE
    WHEN s.seller_state IN ('AC','AP','AM','PA','RO','RR','TO') THEN 'Norte'
    WHEN s.seller_state IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'Nordeste'
    WHEN s.seller_state IN ('DF','GO','MT','MS') THEN 'Centro-Oeste'
    WHEN s.seller_state IN ('ES','MG','RJ','SP') THEN 'Sudeste'
    WHEN s.seller_state IN ('PR','RS','SC') THEN 'Sul'
    ELSE 'Não informado'
  END AS region,
  g.geolocation_lat AS latitude,
  g.geolocation_lng AS longitude
FROM `olist-data-platform-65749.clean_olist.sellers` AS s
LEFT JOIN `olist-data-platform-65749.clean_olist.geolocation` AS g
  ON s.seller_zip_code_prefix = g.geolocation_zip_code_prefix;