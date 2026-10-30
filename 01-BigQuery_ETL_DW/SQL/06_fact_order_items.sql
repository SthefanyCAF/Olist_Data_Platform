CREATE OR REPLACE TABLE `olist-data-platform-65749.dw_olist.fact_order_items` AS
SELECT
  i.order_id,
  i.order_item_id,
  i.product_id,
  i.seller_id,
  o.customer_id,
  DATE(o.order_purchase_timestamp)         AS purchase_date,
  DATE(o.order_delivered_customer_date)    AS delivered_date,
  DATE(o.order_estimated_delivery_date)    AS estimated_delivery_date,
  o.order_status,
  i.price,
  i.freight_value,
  ROUND(i.price + i.freight_value, 2)      AS item_total,
  DATE_DIFF(DATE(o.order_delivered_customer_date),
            DATE(o.order_purchase_timestamp), DAY)     AS delivery_days,
  DATE_DIFF(DATE(o.order_delivered_customer_date),
            DATE(o.order_estimated_delivery_date), DAY) AS delay_days,
  DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date) AS is_late,
  p.main_payment_type,
  p.has_voucher
FROM `olist-data-platform-65749.clean_olist.order_items` AS i
INNER JOIN `olist-data-platform-65749.clean_olist.orders` AS o
  ON i.order_id = o.order_id
LEFT JOIN `olist-data-platform-65749.dw_olist.agg_order_payments` AS p
  ON i.order_id = p.order_id;