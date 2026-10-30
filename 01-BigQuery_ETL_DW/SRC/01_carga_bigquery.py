import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# ==========================================
# CONFIGURAÇÃO DO GOOGLE CLOUD (BIGQUERY)
# ==========================================
PROJECT_ID = "olist-data-platform-65749"
DATASET_ID = f"{PROJECT_ID}.clean_olist"

# O script descobre sozinho onde está: SRC fica dentro da pasta do projeto 1
PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_DADOS = PASTA_PROJETO / "Data" / "Raw"


def achar_chave(nome="gcp-key.json"):
    """Procura credentials/<nome> na pasta do projeto e nas pastas acima dela."""
    for pasta in [PASTA_PROJETO, *PASTA_PROJETO.parents]:
        candidato = pasta / "credentials" / nome
        if candidato.exists():
            return candidato
    raise FileNotFoundError(
        f"Não achei credentials/{nome}. Pasta do projeto: {PASTA_PROJETO}. "
        "Confira o nome do arquivo da chave e se ele está dentro de uma pasta 'credentials'."
    )


if not PASTA_DADOS.exists():
    raise FileNotFoundError(
        f"Não achei a pasta {PASTA_DADOS}. Coloque os 9 CSVs do Olist nela."
    )

caminho_chave = achar_chave()
print(f"🔑 Chave encontrada em: {caminho_chave}")

client = bigquery.Client.from_service_account_json(str(caminho_chave), project=PROJECT_ID)

# Sobrescreve a tabela se ela já existir (pode rodar de novo sem duplicar dados)
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

linhas_enviadas = {}


def enviar(df, nome_tabela):
    """Envia um DataFrame para o BigQuery e guarda quantas linhas foram enviadas."""
    client.load_table_from_dataframe(
        df, f"{DATASET_ID}.{nome_tabela}", job_config=job_config
    ).result()
    linhas_enviadas[nome_tabela] = len(df)
    print(f"   ✅ {nome_tabela}: {len(df):,} linhas".replace(",", "."))


print("🚀 Iniciando o processo de ETL e Carga...")

# ==========================================
# 1. TABELA: PEDIDOS (ORDERS)
# ==========================================
print("📦 Tratando e enviando: Orders...")
df_orders = pd.read_csv(PASTA_DADOS / "olist_orders_dataset.csv")

colunas_data = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for col in colunas_data:
    df_orders[col] = pd.to_datetime(df_orders[col], errors="coerce")

enviar(df_orders, "orders")

# ==========================================
# 2. TABELA: PRODUTOS TRADUZIDOS (PRODUCTS)
# ==========================================
print("🏷️ Tratando e enviando: Products...")
df_products = pd.read_csv(PASTA_DADOS / "olist_products_dataset.csv")
df_translation = pd.read_csv(PASTA_DADOS / "product_category_name_translation.csv")

# Categoria nula vira 'nao_informado'. Medidas nulas continuam nulas (não sabemos o valor).
df_products["product_category_name"] = df_products["product_category_name"].fillna("nao_informado")

# Traduções que faltam no arquivo original
traducoes_faltantes = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_food_preparers",
}

df_products_translated = pd.merge(
    df_products, df_translation, on="product_category_name", how="left"
)
df_products_translated["product_category_name_english"] = (
    df_products_translated["product_category_name_english"]
    .fillna(df_products_translated["product_category_name"].map(traducoes_faltantes))
    .fillna("not_defined")
)

enviar(df_products_translated, "products")

# ==========================================
# 3. TABELA: GEOLOCALIZAÇÃO (GEOLOCATION)
# ==========================================
print("🗺️ Tratando e enviando: Geolocation...")
df_geo = pd.read_csv(PASTA_DADOS / "olist_geolocation_dataset.csv")

# Mantém só pontos dentro do Brasil e usa a mediana (menos sensível a pontos estranhos)
df_geo_br = df_geo[
    df_geo["geolocation_lat"].between(-34, 6)
    & df_geo["geolocation_lng"].between(-74, -34)
]

df_geo_cleaned = (
    df_geo_br.groupby("geolocation_zip_code_prefix")
    .agg(
        {
            "geolocation_lat": "median",
            "geolocation_lng": "median",
            "geolocation_city": "first",
            "geolocation_state": "first",
        }
    )
    .reset_index()
)

enviar(df_geo_cleaned, "geolocation")

# ==========================================
# 4. TABELA: PAGAMENTOS (PAYMENTS)
# ==========================================
print("💳 Tratando e enviando: Payments...")
df_payments = pd.read_csv(PASTA_DADOS / "olist_order_payments_dataset.csv")
df_payments["payment_installments"] = df_payments["payment_installments"].replace(0, 1)

enviar(df_payments, "payments")

# ==========================================
# 5. DEMAIS TABELAS
# ==========================================
tabelas_simples = {
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
}

for nome_tabela, arquivo_csv in tabelas_simples.items():
    print(f"📥 Enviando tabela: {nome_tabela}...")
    df_temp = pd.read_csv(PASTA_DADOS / arquivo_csv)

    if nome_tabela == "order_reviews":
        df_temp["review_creation_date"] = pd.to_datetime(df_temp["review_creation_date"], errors="coerce")
        df_temp["review_answer_timestamp"] = pd.to_datetime(df_temp["review_answer_timestamp"], errors="coerce")
    elif nome_tabela == "order_items":
        df_temp["shipping_limit_date"] = pd.to_datetime(df_temp["shipping_limit_date"], errors="coerce")

    enviar(df_temp, nome_tabela)

# ==========================================
# 6. CONFERÊNCIA: o que foi enviado x o que está no BigQuery
# ==========================================
print("\n🔎 Conferindo as tabelas no BigQuery...")
tudo_certo = True
for nome_tabela, enviadas in linhas_enviadas.items():
    no_bigquery = client.get_table(f"{DATASET_ID}.{nome_tabela}").num_rows
    ok = enviadas == no_bigquery
    tudo_certo = tudo_certo and ok
    print(f"   {'✅' if ok else '❌'} {nome_tabela}: enviadas {enviadas} | no BigQuery {no_bigquery}")

if tudo_certo:
    print("\n✨ COMPLETO! Todas as tabelas limpas foram carregadas no BigQuery.")
else:
    print("\n⚠️ Alguma tabela está com contagem diferente. Confira antes de continuar.")
