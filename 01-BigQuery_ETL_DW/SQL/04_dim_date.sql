CREATE OR REPLACE TABLE `olist-data-platform-65749.dw_olist.dim_date` AS
SELECT
  d                                    AS full_date,
  EXTRACT(YEAR FROM d)                 AS year,
  EXTRACT(QUARTER FROM d)              AS quarter,
  EXTRACT(MONTH FROM d)                AS month,
  FORMAT_DATE('%Y-%m', d)              AS year_month,
  CASE EXTRACT(MONTH FROM d)
    WHEN 1 THEN 'Janeiro'   WHEN 2 THEN 'Fevereiro' WHEN 3 THEN 'Março'
    WHEN 4 THEN 'Abril'     WHEN 5 THEN 'Maio'      WHEN 6 THEN 'Junho'
    WHEN 7 THEN 'Julho'     WHEN 8 THEN 'Agosto'    WHEN 9 THEN 'Setembro'
    WHEN 10 THEN 'Outubro'  WHEN 11 THEN 'Novembro' WHEN 12 THEN 'Dezembro'
  END                                  AS month_name,
  EXTRACT(DAYOFWEEK FROM d)            AS day_of_week,
  CASE EXTRACT(DAYOFWEEK FROM d)
    WHEN 1 THEN 'Domingo'  WHEN 2 THEN 'Segunda-feira' WHEN 3 THEN 'Terça-feira'
    WHEN 4 THEN 'Quarta-feira' WHEN 5 THEN 'Quinta-feira'
    WHEN 6 THEN 'Sexta-feira'  WHEN 7 THEN 'Sábado'
  END                                  AS day_name,
  EXTRACT(DAYOFWEEK FROM d) IN (1, 7) AS is_weekend
FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2016-01-01', DATE '2018-12-31')) AS d;