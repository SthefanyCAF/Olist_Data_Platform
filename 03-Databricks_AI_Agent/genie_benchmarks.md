# Benchmarks do espaço Genie

Perguntas de teste e a consulta SQL de referência de cada uma, para cadastrar na aba **Benchmarks** do espaço Genie.
Estas 8 perguntas **não** foram usadas como exemplo de SQL no espaço, e por isso medem se o Genie acerta o que não foi ensinado.

## Como cadastrar

1. No espaço Genie, clique em **Benchmarks**.
2. Clique em **Add benchmark**.
3. No campo **Question**, escreva a pergunta.
4. No campo **SQL Answer**, cole a consulta de referência da pergunta.
5. Clique em **Run** para conferir o resultado da consulta e depois em **Add benchmark**.
6. Repita para as 8 perguntas.
7. Clique em **Run benchmarks** e, quando terminar, abra a aba **Evaluations** para ver a precisão.

## Perguntas e consultas de referência

### 1. Qual o total de vendas e o número de pedidos?

```sql
SELECT ROUND(SUM(price), 2) AS total_vendas, COUNT(DISTINCT order_id) AS pedidos
FROM workspace.olist_gold.fact_order_items
```

Esperado: 13591643,70 e 98666.

### 2. Qual estado dos clientes mais compra?

```sql
SELECT c.state AS estado, ROUND(SUM(f.price), 2) AS vendas
FROM workspace.olist_gold.fact_order_items f
JOIN workspace.olist_gold.dim_customers c ON f.customer_id = c.customer_id
GROUP BY c.state
ORDER BY vendas DESC
LIMIT 1
```

Esperado: SP, 5202955,05.

### 3. Qual a participação do Sudeste nas vendas?

```sql
SELECT ROUND(100 * SUM(CASE WHEN c.region = 'Sudeste' THEN f.price END) / SUM(f.price), 1) AS pct_sudeste
FROM workspace.olist_gold.fact_order_items f
JOIN workspace.olist_gold.dim_customers c ON f.customer_id = c.customer_id
```

Esperado: 65,4.

### 4. Qual o mês com maior venda?

```sql
SELECT d.year_month AS mes, ROUND(SUM(f.price), 2) AS vendas
FROM workspace.olist_gold.fact_order_items f
JOIN workspace.olist_gold.dim_date d ON f.purchase_date = d.full_date
GROUP BY d.year_month
ORDER BY vendas DESC
LIMIT 1
```

Esperado: 2017-11, 1010271,37.

### 5. Qual a nota média quando a entrega chega no prazo e quando atrasa?

```sql
SELECT is_late AS atrasou, ROUND(AVG(review_score), 2) AS nota_media
FROM workspace.olist_gold.fact_order_items
WHERE delivered_date IS NOT NULL
GROUP BY is_late
ORDER BY is_late
```

Esperado: `false` com 4,21 e `true` com 2,26.

### 6. Qual o tipo de pagamento principal mais usado, em pedidos?

```sql
SELECT main_payment_type AS tipo_pagamento, COUNT(DISTINCT order_id) AS pedidos
FROM workspace.olist_gold.fact_order_items
GROUP BY main_payment_type
ORDER BY pedidos DESC
LIMIT 1
```

Esperado: credit_card, 74479.

### 7. Quais os 3 vendedores que mais vendem?

```sql
SELECT seller_id, ROUND(SUM(price), 2) AS vendas
FROM workspace.olist_gold.fact_order_items
GROUP BY seller_id
ORDER BY vendas DESC
LIMIT 3
```

Esperado: 229472,63, 222776,05 e 200472,92.

### 8. Qual estado tem o maior tempo médio de entrega, considerando só estados com pelo menos 100 itens entregues?

```sql
SELECT c.state AS estado, ROUND(AVG(f.delivery_days), 1) AS media_dias
FROM workspace.olist_gold.fact_order_items f
JOIN workspace.olist_gold.dim_customers c ON f.customer_id = c.customer_id
WHERE f.delivered_date IS NOT NULL
GROUP BY c.state
HAVING COUNT(*) >= 100
ORDER BY media_dias DESC
LIMIT 1
```

Esperado: AM, 26,3.

## Como o Genie classifica as respostas

- **Good:** o resultado gerado é igual ao da consulta de referência (ou os números arredondam para os mesmos 4 dígitos significativos).
- **Bad:** a consulta gerada dá erro, devolve resultado vazio ou um valor único diferente.
- **Manual review:** o Genie não conseguiu avaliar sozinho, por exemplo quando o resultado não traz uma correspondência exata. Nesse caso, abra a resposta e marque você mesma como Good ou Bad, para a precisão final ficar correta.

## Registro

Os detalhes de cada avaliação ficam visíveis por uma semana, por isso faça o print da tela de **Evaluations** logo depois de rodar e salve em `Docs/genie_benchmarks.png`.
