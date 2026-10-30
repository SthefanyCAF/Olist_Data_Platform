CREATE OR REPLACE TABLE `olist-data-platform-65749.dw_olist.dim_products` AS
SELECT
  product_id,
  product_category_name          AS category_pt,
  product_category_name_english  AS category_en,
  product_weight_g               AS weight_g,
  product_length_cm              AS length_cm,
  product_height_cm              AS height_cm,
  product_width_cm               AS width_cm,
  product_photos_qty             AS photos_qty
FROM `olist-data-platform-65749.clean_olist.products`;