# Espaço Genie: Olist Vendas e Entregas

Configuração do espaço Genie do projeto 3. Este arquivo guarda o que foi colado no Databricks, para a configuração ficar documentada e reproduzível.

## Tabelas do espaço

Schema `workspace.olist_gold`:

- `fact_order_items`
- `dim_products`
- `dim_customers`
- `dim_sellers`
- `dim_date`
- `agg_order_payments`

Ficam de fora `data_quality_results` e `fact_order_items_inc`, que não servem para perguntas de negócio.

## Relações entre tabelas (Joins)

| Tabela (muitos) | Coluna | Tabela (um) | Coluna |
|---|---|---|---|
| `fact_order_items` | `product_id` | `dim_products` | `product_id` |
| `fact_order_items` | `seller_id` | `dim_sellers` | `seller_id` |
| `fact_order_items` | `customer_id` | `dim_customers` | `customer_id` |
| `fact_order_items` | `purchase_date` | `dim_date` | `full_date` |
| `fact_order_items` | `order_id` | `agg_order_payments` | `order_id` |

## Instruções gerais (aba Text)

```
Responda sempre em português do Brasil.
Os dados são vendas de um marketplace brasileiro entre setembro de 2016 e outubro de 2018.
Vendas ou faturamento = SUM(price) da tabela fact_order_items. O frete fica em freight_value e não entra em vendas.
Pedidos = COUNT(DISTINCT order_id). Itens vendidos = número de linhas de fact_order_items.
Ticket médio = vendas dividido por pedidos distintos.
Clientes distintos = COUNT(DISTINCT customer_unique_id) em dim_customers, pois customer_id muda a cada pedido.
Percentual de atraso = itens com is_late verdadeiro dividido por itens com delivered_date preenchida. Ignore pedidos não entregues nessa conta.
Tempo de entrega = delivery_days, considerando só itens entregues.
Para agrupar por categoria use dim_products.category_en. Para agrupar por mês use dim_date.year_month.
Região e estado do cliente vêm de dim_customers. Região e estado do vendedor vêm de dim_sellers. Quando a pergunta falar de estado ou região sem dizer de quem, use o do cliente.
Valores pagos devem vir de agg_order_payments, e nunca de somar pagamentos junto com os itens da tabela fato.
Formate valores em reais com duas casas decimais e percentuais com uma casa decimal.
```

## Exemplos de SQL (aba SQL Queries)

Só três perguntas viram exemplo. As outras ficam reservadas como teste (benchmarks), para medir se o Genie acerta o que não foi ensinado.

### Exemplo 1: "Quais as 5 categorias que mais vendem?"

```sql
SELECT
  p.category_en          AS categoria,
  ROUND(SUM(f.price), 2) AS vendas
FROM workspace.olist_gold.fact_order_items AS f
JOIN workspace.olist_gold.dim_products AS p ON f.product_id = p.product_id
GROUP BY p.category_en
ORDER BY vendas DESC
LIMIT 5
```

### Exemplo 2: "Qual o percentual de itens entregues com atraso?"

```sql
SELECT
  COUNT_IF(is_late)                    AS itens_atrasados,
  COUNT_IF(delivered_date IS NOT NULL) AS itens_entregues,
  ROUND(100 * COUNT_IF(is_late) / COUNT_IF(delivered_date IS NOT NULL), 1) AS pct_atraso
FROM workspace.olist_gold.fact_order_items
```

### Exemplo 3: "Qual o ticket médio?"

```sql
SELECT
  ROUND(SUM(price) / COUNT(DISTINCT order_id), 2) AS ticket_medio
FROM workspace.olist_gold.fact_order_items
```

## Perguntas de teste (benchmarks)

| # | Pergunta | Resposta esperada |
|---|---|---|
| 1 | Qual o total de vendas e o número de pedidos? | R$ 13.591.643,70 e 98.666 pedidos |
| 3 | Qual estado dos clientes mais compra? | SP, R$ 5.202.955,05 |
| 4 | Qual a participação do Sudeste nas vendas? | 65,4% |
| 5 | Qual o mês com maior venda? | 2017-11, R$ 1.010.271,37 |
| 7 | Qual a nota média quando a entrega chega no prazo e quando atrasa? | 4,21 e 2,26 |
| 8 | Qual o tipo de pagamento principal mais usado, em pedidos? | credit_card, 74.479 pedidos |
| 10 | Quais os 3 vendedores que mais vendem? | R$ 229.472,63, R$ 222.776,05 e R$ 200.472,92 |
| Bônus | Qual estado tem o maior tempo médio de entrega, com pelo menos 100 itens entregues? | AM, 26,3 dias |