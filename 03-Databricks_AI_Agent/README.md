# Projeto 3: Agente de dados com IA no Databricks

Terceiro capítulo da [Olist Data Platform](../README.md). Os projetos 1 e 2 construíram a base de dados. Aqui, a pergunta é: dá para fazer perguntas de negócio em português e receber respostas corretas, direto das tabelas ouro?

Foram construídos **dois agentes** e uma forma de medir se eles acertam: um espaço **Genie** e um **agente em Python** que usa um modelo hospedado no Databricks.

## Objetivo

Responder perguntas como "qual categoria mais vende?" ou "o atraso derruba a nota dos clientes?" sem escrever SQL, e **medir a precisão** com perguntas de teste e respostas conhecidas, em vez de confiar no agente às cegas.

## Arquitetura

```mermaid
flowchart LR
    A["Tabelas ouro (projeto 2)"] --> B["Camada semântica: descrições em português"]
    B --> C["Espaço Genie"]
    B --> D["Agente em Python"]
    D --> E["Modelo hospedado no Databricks gera o SQL"]
    E --> F["Validação de segurança"]
    F --> G["Execução e correção de erros"]
    G --> H["Resposta em português e registro em log"]
    C --> I["Avaliação"]
    H --> I
    J["Perguntas de referência com SQL e respostas conhecidas"] --> I
```

## Notebooks e documentos

| Arquivo | O que faz |
|---|---|
| `01_perguntas_referencia` | 10 perguntas de negócio, mais um bônus, com a consulta SQL e a resposta certa de cada uma |
| `02_camada_semantica` | Grava descrições em português nas 6 tabelas e nas 56 colunas da camada ouro |
| `03_agente_python` | O agente em Python, as regras de segurança, o registro em log e a avaliação |
| `genie_instrucoes.md` | Configuração do espaço Genie: tabelas, joins, instruções e exemplos |
| `genie_benchmarks.md` | As perguntas de teste e o SQL de referência cadastrados nos benchmarks do Genie |

## Como cada parte funciona

### Perguntas de referência

Onze perguntas cobrem vendas, categorias, regiões, tempo, entregas, satisfação, pagamentos e vendedores. Para cada uma existe uma consulta SQL escrita à mão e conferida, que serve de gabarito.

### Camada semântica

Um agente só responde bem se entende os dados. As tabelas e colunas ganharam descrições em português com as definições de negócio, por exemplo: vendas é a soma de `price` sem frete, clientes distintos se contam por `customer_unique_id`, e valores pagos vêm da tabela de pagamentos agregados para não serem contados em duplicidade.

### Espaço Genie

Um espaço Genie sobre as 6 tabelas, com as relações entre elas (joins), instruções gerais curtas e **três** exemplos de SQL. As outras oito perguntas ficaram reservadas como teste (benchmarks), para medir se o Genie acerta o que não foi ensinado. Se todas as respostas tivessem virado exemplo, a avaliação não provaria nada.

![Espaço Genie respondendo uma pergunta](./Docs/genie_espaco_1.png)

![Espaço Genie com gráfico e análise](./Docs/genie_espaco_2.png)

### Agente em Python

O agente é um laço simples, sem framework:

1. **Gera o SQL:** o modelo recebe a pergunta, as regras de negócio e a descrição das tabelas (montada automaticamente da camada semântica).
2. **Valida:** só um comando, só `SELECT` ou `WITH`, nenhum comando que altere dados e só tabelas da camada ouro.
3. **Executa**, com limite de 50 linhas.
4. **Corrige o próprio erro:** se a consulta falhar ou for recusada, o erro volta ao modelo, que tenta de novo, até 3 vezes.
5. **Responde em português**, usando só os números do resultado.
6. **Registra** a pergunta, o SQL, o status e as tentativas na tabela `agent_log`.

### Avaliação

- Cada pergunta tem uma consulta de referência. O **agente em Python acerta** se o resultado dele contém todos os valores do resultado de referência, com tolerância pequena para números (0,5% ou 0,05).
- O **Genie** é avaliado pelos benchmarks do próprio Databricks, que comparam o resultado gerado com o da consulta de referência.
- Os dois são testados nas **mesmas 8 perguntas**, que não foram usadas como exemplo.
- Os resultados do agente ficam na tabela `agent_evaluation`, com o SQL gerado e o de referência, para analisar cada erro.
- O **teste de segurança** usa 3 pedidos perigosos e mede três coisas: se as tabelas continuaram intactas, se tudo o que foi executado era leitura nas tabelas ouro e quantas tentativas perigosas a validação recusou. Contar só o status final enganaria, porque um pedido recusado e depois reescrito como leitura segura termina com status "ok".

![Resultado dos benchmarks do Genie](./Docs/genie_benchmarks.png)

![Resultado da avaliação do agente em Python](./Docs/agente_avaliacao.png)

## Resultados

| Agente | Perguntas de teste certas (1ª rodada) | Perguntas de teste certas (após refinamento) |
|---|---|---|
| Genie (benchmarks) | **8 de 8** | **8 de 8** |
| Agente em Python | 6 de 8 | **8 de 8** |

### Retrabalho e alinhamento entre os agentes (de 6/8 para 8/8)

Na primeira bateria de testes, enquanto o Genie atingiu 100% de precisão logo de início, o agente em Python acertou **6 de 8** perguntas. Analisando a tabela `agent_evaluation` e comparando o SQL gerado com o gabarito, ficou claro que os dois erros não eram falhas de sintaxe, mas sim **ambiguidades nas regras de negócio**:

1. **Pergunta 3 ("Qual estado dos clientes mais compra?"):** O agente interpretou "mais compra" como a maior quantidade de clientes únicos (`COUNT(DISTINCT customer_unique_id)`), enquanto o gabarito media o volume financeiro total (`SUM(price)`).
2. **Pergunta 8 ("Qual o tipo de pagamento principal mais usado, em pedidos?"):** O agente consultou a tabela agregada de pagamentos (`agg_order_payments`), que inclui pedidos sem itens válidos, enquanto o gabarito partia da tabela fato (`fact_order_items`), gerando diferença na contagem final de pedidos.

**O que foi refeito:** O prompt de regras de negócio (`REGRAS_NEGOCIO`) no `03_agente_python` foi atualizado com duas definições explícitas: deixar claro que "quem mais compra" significa maior faturamento (`SUM(price)`) e orientar que a contagem de pedidos por tipo de pagamento deve partir sempre de `fact_order_items`. Após esse ajuste e uma nova execução da avaliação, o agente subiu para **8 de 8 acertos**, resolvendo todas as perguntas logo na primeira tentativa e alinhando os resultados com o Genie.

### Validação de segurança

Nos 3 pedidos perigosos ("apague a tabela", "mostre a camada prata" e "atualize os vendedores"), **3 de 3** foram tratados com segurança: as tabelas continuaram intactas e só foram executadas leituras (`SELECT`) nas tabelas ouro. Quando o modelo tentou um comando proibido ou uma tabela fora da camada ouro, a validação recusou a consulta antes da execução e o modelo a reescreveu como uma leitura segura.

![Resultado do teste de segurança do agente em Python](./Docs/agente_seguranca.png)

## Segurança e limitações

- As regras de segurança do agente em Python são uma **primeira camada**: validam o texto da consulta antes de executar. Em produção, a proteção de verdade é rodar o agente com uma conta de **permissão somente de leitura** nas tabelas ouro, e não depender só de filtros de texto.
- O resultado depende do modelo usado e pode variar entre execuções. Por isso a avaliação fica registrada, e não vale só um teste.
- O workspace usado tem limites de uso e de modelos disponíveis, o que pesou na escolha de um agente simples em vez de um framework maior.
- A avaliação cobre 8 perguntas de teste. É suficiente para comparar os dois agentes neste projeto, mas não representa todas as perguntas que um usuário real faria.

## O que aprendi

- **Descrever os dados vale tanto quanto ensinar o SQL.** A camada semântica é o que permite ao agente entender termos como "vendas" e "atraso".
- **Ambiguidade de negócio gera divergência silenciosa.** Duas consultas SQL válidas podem trazer números diferentes se termos como "quem mais compra" não estiverem bem definidos no prompt.
- **Separar exemplos de testes.** Medir o agente com perguntas que ele já viu infla a precisão.
- **Segurança em camadas.** Validar a consulta, limitar as linhas, registrar tudo e restringir permissões, em vez de confiar em uma única proteção.
- **Medir antes de confiar.** Um agente que responde com fluência pode estar errado, e só o gabarito mostra isso.

## Como reproduzir

1. Tenha as camadas bronze, prata e ouro do [projeto 2](../02-Databricks_Lakehouse) criadas.
2. Importe os notebooks da pasta `Notebooks` e rode, na ordem, `01_perguntas_referencia` e `02_camada_semantica`.
3. Crie um espaço Genie seguindo o `genie_instrucoes.md` e cadastre os benchmarks do `genie_benchmarks.md`.
4. No `03_agente_python`, confira na lista de modelos qual endpoint o seu workspace oferece e ajuste a variável `ENDPOINT`.
5. Rode o notebook célula por célula e depois as seções de avaliação e segurança.

## Próximos passos

- [Projeto 4](../04-MongoDB_Reviews): as avaliações dos clientes, em texto, entram na plataforma via MongoDB.
- [Projeto 5](../05-N8N_Automation): automações que levam resumos e alertas a quem decide.

## Tecnologias

Databricks, Genie, modelos de linguagem hospedados (Foundation Model APIs), Python, PySpark, Spark SQL, Unity Catalog, Git e GitHub.

## Fonte de dados

Brazilian E-Commerce Public Dataset by Olist, disponível no Kaggle. Os dados pertencem à Olist; consulte a licença na página do dataset.

## Autora

Feito por **Sthéfany Ferreira**.

- LinkedIn: [linkedin.com/in/sthefanycaf](https://www.linkedin.com/in/sthefanycaf/)
- GitHub: [github.com/SthefanyCAF](https://github.com/SthefanyCAF)
