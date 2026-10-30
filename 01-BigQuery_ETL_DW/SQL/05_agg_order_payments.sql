CREATE OR REPLACE TABLE `olist-data-platform-65749.dw_olist.agg_order_payments` AS
SELECT
  order_id,
  ROUND(SUM(payment_value), 2)    AS total_paid,
  COUNT(*)                        AS payment_count,
  MAX(payment_installments)       AS max_installments,
  ARRAY_AGG(payment_type
            ORDER BY payment_value DESC, payment_sequential ASC
            LIMIT 1)[OFFSET(0)]   AS main_payment_type,
  LOGICAL_OR(payment_type = 'voucher') AS has_voucher
FROM `olist-data-platform-65749.clean_olist.payments`
GROUP BY order_id;