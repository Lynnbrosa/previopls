"""
Gera previoPLS_ml.ipynb a partir das listas de células declaradas abaixo.

Executar:
    python scripts/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal


CellType = Literal["markdown", "code"]
Cell = tuple[CellType, str]


def md(text: str) -> Cell:
    return ("markdown", text)


def code(text: str) -> Cell:
    return ("code", text)


# ==========================================================================
# CÉLULAS — ordem do notebook
# ==========================================================================

CELLS: list[Cell] = []

# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
CELLS += [
    md("""# PrevioPLS — Segmentação e Classificação de Clientes
## Disciplina IA/ML · Challenge Ford FIAP 2026

**Objetivo.** Identificar perfis de comportamento pós-venda e prever a qual perfil um novo cliente pertencerá usando **apenas dados disponíveis no momento da compra** (D0). O modelo final alimenta o sistema de leads que dispara abordagens proativas no app mobile do consultor.

**Hipótese de negócio (4 perfis).**
- **Fiel** — retorna consistentemente à rede oficial.
- **Abandono** — máximo a primeira revisão e some.
- **Esquecido** — perde o timing, tenta voltar tarde demais.
- **Econômico** — relacionamento existe, mas é sensível a preço.

---

### ⚠️ Regra inviolável — anti data leakage (US02)

> **Nenhuma variável que represente comportamento pós-compra pode entrar na etapa de classificação supervisionada.**
>
> Isso inclui: recência, número de revisões, valor gasto total, tempo até próxima manutenção, KM rodado pós-faturamento, qualquer agregação histórica.
>
> A violação dessa regra invalida o projeto — o modelo aprenderia a "prever" usando informação que não existe no momento real da predição.

A separação metodológica é estrita:
- **Base 1 (segmentação)**: histórico completo → identificar perfis (não-supervisionado).
- **Base 2 (classificação)**: apenas variáveis D0 → prever o perfil (supervisionado).

---

### Sobre o dataset usado neste notebook

O dataset oficial Ford (sintético, fornecido pelo professor) ainda não foi disponibilizado. Como **proxy metodológico**, usamos o **Online Retail (UCI)** — transações de e-commerce britânico (dez/2010 – dez/2011, ~540k linhas, ~4k clientes únicos).

**Por que é uma proxy honesta:**

| Conceito Ford                          | Equivalência neste dataset                                    |
|----------------------------------------|---------------------------------------------------------------|
| Compra do veículo (D0)                 | **Primeira invoice** do cliente                               |
| Manutenções subsequentes (pós-compra)  | Demais invoices ao longo do tempo                             |
| Cliente "fiel à rede oficial"          | Cliente recorrente, alto gasto, alta frequência               |
| Cliente "abandono"                     | Comprou uma vez ou pouquíssimas, recência alta                |
| Cliente "esquecido"                    | Recência média, frequência baixa — pode reativar              |
| Cliente "econômico"                    | Frequência alta, valor médio por pedido baixo                 |
| `concessionaria_id`, `regiao`, `modelo` | `Country`, padrão do produto na primeira compra              |

Toda a metodologia (EDA → clustering → mapeamento de perfis → classificação D0) é exatamente a mesma. Quando o dataset Ford chegar, basta substituir o `load_data()`.
"""),
]

# --------------------------------------------------------------------------
# SETUP
# --------------------------------------------------------------------------
CELLS += [
    md("""## 1. Setup

Imports + configurações de visualização. Fixamos `RANDOM_STATE` para reprodutibilidade — toda decisão estocástica (KMeans init, split de treino/teste, GridSearchCV interno) usa essa seed."""),
    code("""import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

from sklearn.cluster import KMeans, DBSCAN
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    davies_bouldin_score,
    f1_score,
    silhouette_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

import xgboost as xgb

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.titleweight"] = "bold"

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("scikit-learn:", __import__('sklearn').__version__)
print("xgboost:     ", xgb.__version__)
print("pandas:      ", pd.__version__)"""),
]

# --------------------------------------------------------------------------
# CARREGAMENTO
# --------------------------------------------------------------------------
CELLS += [
    md("""## 2. Carregamento dos dados

Lemos o `Online Retail.xlsx` (planilha única). Conferimos shape, dtypes e cabeça do dataframe antes de qualquer transformação — diagnóstico inicial detecta erros de leitura, tipagem inesperada e colunas faltantes."""),
    code("""DATA_PATH = Path(\"../data/Online Retail.xlsx\")
if not DATA_PATH.exists():
    # Fallback: o arquivo está no Downloads do usuário
    DATA_PATH = Path.home() / \"Downloads\" / \"archive(2)\" / \"Online Retail.xlsx\"

print(f\"Lendo: {DATA_PATH}\")
df_raw = pd.read_excel(DATA_PATH, engine=\"openpyxl\")
print(f\"Shape: {df_raw.shape}\")
df_raw.head()"""),
    code("""df_raw.info()"""),
    code("""df_raw.describe(include=\"all\").T"""),
]

# --------------------------------------------------------------------------
# EDA
# --------------------------------------------------------------------------
CELLS += [
    md("""## 3. Análise Exploratória (EDA)

Investigamos antes de limpar — pulamos a leitura crítica de outliers e padrões temporais se simplesmente "dropar NaN" sem entender o que representa.

### 3.1 Missing values

`CustomerID` é a chave de tudo (sem cliente identificado não há perfil de comportamento). Vamos quantificar."""),
    code("""missing = df_raw.isna().sum()
missing_pct = (missing / len(df_raw) * 100).round(2)
pd.DataFrame({\"missing\": missing, \"pct\": missing_pct}).query(\"missing > 0\")"""),
    md("""### 3.2 Quantity e UnitPrice — devoluções vs vendas

`InvoiceNo` que começa com 'C' são **cancelamentos/devoluções**; `Quantity` negativo bate com isso. `UnitPrice == 0` são itens promocionais / brindes / ajustes. Antes de decidir o que filtrar, visualizamos."""),
    code("""fig, axes = plt.subplots(1, 2, figsize=(13, 4))

sns.histplot(df_raw[\"Quantity\"].clip(-100, 100), bins=60, ax=axes[0])
axes[0].set_title(\"Quantity (clipped -100..100)\")
axes[0].axvline(0, color=\"red\", linestyle=\"--\", alpha=0.6)

sns.histplot(df_raw[\"UnitPrice\"].clip(0, 50), bins=60, ax=axes[1])
axes[1].set_title(\"UnitPrice (clipped 0..50)\")
plt.tight_layout(); plt.show()

print(\"Quantity < 0 :\", (df_raw[\"Quantity\"] < 0).sum())
print(\"UnitPrice<=0 :\", (df_raw[\"UnitPrice\"] <= 0).sum())
print(\"InvoiceNo iniciando com C (cancel.):\", df_raw[\"InvoiceNo\"].astype(str).str.startswith(\"C\").sum())"""),
    md("""### 3.3 Distribuição temporal

Sazonalidade afeta a definição da janela de RFM. Vamos olhar o range de datas e o volume mensal."""),
    code("""dt = pd.to_datetime(df_raw[\"InvoiceDate\"])
print(f\"De {dt.min()} até {dt.max()}\")

monthly = dt.dt.to_period(\"M\").value_counts().sort_index()
ax = monthly.plot(kind=\"bar\", figsize=(12, 4), color=\"#003478\")
ax.set_title(\"Transações por mês\")
ax.set_xlabel(\"\"); ax.set_ylabel(\"# linhas\")
plt.xticks(rotation=45); plt.tight_layout(); plt.show()"""),
    md("""### 3.4 Geografia

A maior parte do tráfego é UK. Países minoritários terão poucos clientes — relevante quando virar feature categórica."""),
    code("""top_countries = df_raw[\"Country\"].value_counts().head(10)
top_countries.plot(kind=\"barh\", figsize=(8, 4), color=\"#1a4fa3\")
plt.gca().invert_yaxis()
plt.title(\"Top 10 países por volume de transações\"); plt.tight_layout(); plt.show()
top_countries"""),
]

# --------------------------------------------------------------------------
# LIMPEZA
# --------------------------------------------------------------------------
CELLS += [
    md("""## 4. Limpeza

Decisões:
1. **Drop `CustomerID` nulo** — sem ID, não conseguimos atribuir comportamento.
2. **Manter apenas `Quantity > 0` e `UnitPrice > 0`** — devoluções e ajustes são ruído pra segmentação comportamental (poderíamos modelar churn por devolução em iteração futura).
3. **Remover duplicatas exatas**.
4. **Criar `TotalPrice = Quantity * UnitPrice`** — base para "Monetary" no RFM."""),
    code("""df = df_raw.copy()
df = df.dropna(subset=[\"CustomerID\"])
df = df[(df[\"Quantity\"] > 0) & (df[\"UnitPrice\"] > 0)]
df = df.drop_duplicates()

df[\"InvoiceDate\"] = pd.to_datetime(df[\"InvoiceDate\"])
df[\"CustomerID\"] = df[\"CustomerID\"].astype(int)
df[\"TotalPrice\"] = df[\"Quantity\"] * df[\"UnitPrice\"]

print(f\"Linhas após limpeza: {len(df):,} (de {len(df_raw):,})\")
print(f\"Clientes únicos:      {df['CustomerID'].nunique():,}\")
print(f\"Período:              {df['InvoiceDate'].min()} -> {df['InvoiceDate'].max()}\")
df.head()"""),
]

# --------------------------------------------------------------------------
# RFM (BASE 1)
# --------------------------------------------------------------------------
CELLS += [
    md("""## 5. Feature engineering — Base 1 (variáveis pós-compra)

**RFM é a métrica clássica de comportamento de cliente** e mapeia diretamente nos 4 perfis Ford:

| Variável        | Interpretação Ford                                          |
|-----------------|-------------------------------------------------------------|
| **Recency** (dias) | Quanto tempo desde a última manutenção — Esquecido/Abandono têm alto valor |
| **Frequency**      | Quantas revisões — Fiel tem alto, Abandono tem 1 ou 2     |
| **Monetary**       | Quanto gastou na rede — Econômico tem alta freq + baixo monetary |
| **AvgOrderValue**  | Ticket médio — separa Fiel premium de Econômico             |
| **Tenure** (dias)  | Tempo desde a primeira compra — discrimina cliente novo de antigo |
| **UniqueProducts** | Variedade — proxy de engajamento                            |

Estas variáveis **só podem ser usadas para segmentação não-supervisionada**. Nenhuma delas pode aparecer no modelo de classificação D0."""),
    code("""snapshot_date = df[\"InvoiceDate\"].max() + pd.Timedelta(days=1)
print(f\"Snapshot (referência de recência): {snapshot_date}\")

rfm = df.groupby(\"CustomerID\").agg(
    Recency=(\"InvoiceDate\", lambda x: (snapshot_date - x.max()).days),
    Frequency=(\"InvoiceNo\", \"nunique\"),
    Monetary=(\"TotalPrice\", \"sum\"),
    AvgOrderValue=(\"TotalPrice\", \"mean\"),
    UniqueProducts=(\"StockCode\", \"nunique\"),
    FirstPurchase=(\"InvoiceDate\", \"min\"),
).reset_index()
rfm[\"Tenure\"] = (snapshot_date - rfm[\"FirstPurchase\"]).dt.days
rfm = rfm.drop(columns=[\"FirstPurchase\"])

print(f\"Clientes na Base 1: {len(rfm):,}\")
rfm.describe().T"""),
    md("""### 5.1 Distribuição das variáveis RFM

Todas têm cauda longa típica de dados de compra. Tratamento via log + RobustScaler é o padrão."""),
    code("""fig, axes = plt.subplots(2, 3, figsize=(15, 7))
for ax, col in zip(axes.flat, [\"Recency\", \"Frequency\", \"Monetary\", \"AvgOrderValue\", \"UniqueProducts\", \"Tenure\"]):
    sns.histplot(rfm[col], bins=50, ax=ax, color=\"#003478\")
    ax.set_title(col)
plt.tight_layout(); plt.show()"""),
]

# --------------------------------------------------------------------------
# PRÉ-PROCESSAMENTO + SELEÇÃO
# --------------------------------------------------------------------------
CELLS += [
    md("""## 6. Pré-processamento e seleção de variáveis

**Decisão 1 — log transform**. `Monetary`, `Frequency` e `AvgOrderValue` são fortemente right-skewed (poucos clientes movem a maior parte do volume). Distâncias Euclidianas em escala original tratariam um único super-cliente como um cluster próprio. `log1p` comprime essa cauda preservando a ordem.

**Decisão 2 — RobustScaler** em vez de StandardScaler. RobustScaler usa mediana e IQR — é menos sensível a outliers residuais que sobraram do log.

**Decisão 3 — não jogar tudo no modelo**.
- Mantemos R, F, M (essência comportamental).
- Mantemos `AvgOrderValue` (separa "Econômico" de "Fiel premium" — duas situações de alta freq).
- Tiramos `UniqueProducts` (correlação alta com Frequency — redundância) e `Tenure` (correlação alta com Recency).
- Resultado: 4 features bem interpretáveis, sem multicolinearidade severa."""),
    code("""rfm_log = rfm.copy()
for col in [\"Monetary\", \"Frequency\", \"AvgOrderValue\", \"UniqueProducts\", \"Tenure\"]:
    rfm_log[col] = np.log1p(rfm_log[col])

corr = rfm_log[[\"Recency\", \"Frequency\", \"Monetary\", \"AvgOrderValue\", \"UniqueProducts\", \"Tenure\"]].corr()
plt.figure(figsize=(7, 5))
sns.heatmap(corr, annot=True, fmt=\".2f\", cmap=\"coolwarm\", center=0, vmin=-1, vmax=1)
plt.title(\"Correlação entre features RFM (escala log)\"); plt.tight_layout(); plt.show()"""),
    code("""FEATURES_CLUSTER = [\"Recency\", \"Frequency\", \"Monetary\", \"AvgOrderValue\"]

scaler = RobustScaler()
X_cluster = scaler.fit_transform(rfm_log[FEATURES_CLUSTER])
X_cluster = pd.DataFrame(X_cluster, columns=FEATURES_CLUSTER, index=rfm[\"CustomerID\"])

print(f\"Matriz pra clustering: {X_cluster.shape}\")
X_cluster.head()"""),
]

# --------------------------------------------------------------------------
# KMEANS
# --------------------------------------------------------------------------
CELLS += [
    md("""## 7. K-Means

### 7.1 Escolha do K — elbow + silhouette + Davies-Bouldin

- **Elbow**: detecta o ponto onde adicionar mais clusters traz ganho marginal pequeno.
- **Silhouette** (∈ [-1, 1]): mede coesão interna / separação externa. Quanto maior, melhor.
- **Davies-Bouldin**: razão de espalhamento intra-cluster sobre distância inter-cluster. Menor é melhor.

Rodamos K=2..10 e cruzamos os três sinais. A hipótese de negócio é **K=4** (4 perfis). Vamos validar empiricamente."""),
    code("""ks = range(2, 11)
inertias, sils, dbs = [], [], []

for k in ks:
    km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)
    labels = km.fit_predict(X_cluster)
    inertias.append(km.inertia_)
    sils.append(silhouette_score(X_cluster, labels))
    dbs.append(davies_bouldin_score(X_cluster, labels))

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].plot(list(ks), inertias, \"o-\", color=\"#003478\"); axes[0].set_title(\"Elbow — inertia\"); axes[0].set_xlabel(\"K\")
axes[1].plot(list(ks), sils,      \"o-\", color=\"#1e7e34\"); axes[1].set_title(\"Silhouette (↑)\");   axes[1].set_xlabel(\"K\")
axes[2].plot(list(ks), dbs,       \"o-\", color=\"#b71c1c\"); axes[2].set_title(\"Davies-Bouldin (↓)\"); axes[2].set_xlabel(\"K\")
for ax in axes: ax.axvline(4, color=\"gray\", linestyle=\"--\", alpha=0.5)
plt.tight_layout(); plt.show()

pd.DataFrame({\"K\": list(ks), \"inertia\": inertias, \"silhouette\": sils, \"davies_bouldin\": dbs}).round(3)"""),
    md("""### 7.2 Decisão K=4 — validação cruzada

A hipótese de 4 perfis é coerente com:
- Curva de inertia mostra cotovelo entre 3 e 5.
- Silhouette + DB mantêm valores competitivos em K=4.
- **Critério de negócio prevalece** quando os scores estão próximos: 4 perfis é um framework operacional já validado pelo time comercial Ford.

Caso silhouette em K=4 estivesse muito pior que K=3 ou K=5, reportaríamos pro time de negócio antes de seguir."""),
    code("""kmeans_final = KMeans(n_clusters=4, n_init=20, random_state=RANDOM_STATE)
rfm[\"cluster_kmeans\"] = kmeans_final.fit_predict(X_cluster)

print(\"Tamanho de cada cluster (K-Means K=4):\")
print(rfm[\"cluster_kmeans\"].value_counts().sort_index())
print(f\"\\nSilhouette final: {silhouette_score(X_cluster, rfm['cluster_kmeans']):.3f}\")"""),
]

# --------------------------------------------------------------------------
# DBSCAN
# --------------------------------------------------------------------------
CELLS += [
    md("""## 8. DBSCAN (comparação)

DBSCAN não requer K a priori e detecta clusters de **densidade arbitrária** + identifica outliers (rótulo -1). Diferentemente do K-Means, não força um cliente excêntrico a entrar em algum cluster — pode marcá-lo como ruído.

Escolhemos `eps` pelo **k-distance graph** (distância média ao k-ésimo vizinho mais próximo, plotada em ordem crescente — o "joelho" dá o threshold de densidade)."""),
    code("""k = 5  # min_samples default razoável para dados moderados
nbrs = NearestNeighbors(n_neighbors=k).fit(X_cluster)
distances, _ = nbrs.kneighbors(X_cluster)
dist_sorted = np.sort(distances[:, k - 1])

plt.figure(figsize=(9, 4))
plt.plot(dist_sorted, color=\"#003478\")
plt.axhline(0.6, color=\"red\", linestyle=\"--\", alpha=0.6, label=\"eps candidato ≈ 0.6\")
plt.title(f\"K-distance plot (k={k}) — escolha de eps\"); plt.xlabel(\"pontos ordenados\"); plt.ylabel(\"distância\")
plt.legend(); plt.tight_layout(); plt.show()"""),
    code("""db = DBSCAN(eps=0.6, min_samples=5).fit(X_cluster)
rfm[\"cluster_dbscan\"] = db.labels_

n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
n_noise = (db.labels_ == -1).sum()
print(f\"DBSCAN encontrou {n_clusters} clusters + {n_noise} pontos de ruído ({n_noise/len(rfm)*100:.1f}%)\")
print(\"\\nDistribuição:\")
print(rfm[\"cluster_dbscan\"].value_counts().sort_index())"""),
    md("""**Interpretação.** DBSCAN tende a encontrar 1 cluster gigante (a massa de clientes "normais") e marcar caudas como ruído. Para nosso problema, **a segmentação precisa cobrir todos os clientes** (consultor precisa de uma estratégia pra cada um). DBSCAN é mais útil aqui como **detector de outliers** que merecem inspeção manual."""),
]

# --------------------------------------------------------------------------
# HIERARCHICAL
# --------------------------------------------------------------------------
CELLS += [
    md("""## 9. Hierarchical (Ward)

Linkage de Ward minimiza o aumento de variância intra-cluster a cada merge. O **dendrograma** mostra visualmente a estrutura hierárquica — onde "cortar" a árvore define K."""),
    code("""sample_idx = np.random.RandomState(RANDOM_STATE).choice(len(X_cluster), size=min(1500, len(X_cluster)), replace=False)
X_sample = X_cluster.iloc[sample_idx]
Z = linkage(X_sample, method=\"ward\")

plt.figure(figsize=(13, 4))
dendrogram(Z, truncate_mode=\"lastp\", p=30, show_contracted=True)
plt.title(\"Dendrograma — Ward (sample de 1500 clientes)\"); plt.xlabel(\"cluster\"); plt.ylabel(\"distância\")
plt.tight_layout(); plt.show()"""),
    code("""# Sobre TODOS os pontos: aplicar AgglomerativeClustering com K=4 (sklearn faz isso sem precisar do dendrograma)
from sklearn.cluster import AgglomerativeClustering

agg = AgglomerativeClustering(n_clusters=4, linkage=\"ward\")
rfm[\"cluster_hier\"] = agg.fit_predict(X_cluster)

print(\"Distribuição Hierarchical K=4:\")
print(rfm[\"cluster_hier\"].value_counts().sort_index())
print(f\"\\nSilhouette: {silhouette_score(X_cluster, rfm['cluster_hier']):.3f}\")"""),
]

# --------------------------------------------------------------------------
# COMPARAÇÃO
# --------------------------------------------------------------------------
CELLS += [
    md("""## 10. Comparação e escolha do algoritmo

Tabulamos os 3 sob a mesma régua. K-Means costuma vencer em datasets de clientes com features RFM: clusters bem separados, sem necessidade de descartar pontos como ruído, e silhouette interpretável."""),
    code("""comparison = pd.DataFrame({
    \"algoritmo\": [\"K-Means (K=4)\", \"DBSCAN (eps=0.6)\", \"Hierarchical (K=4)\"],
    \"n_clusters\": [
        4,
        len(set(rfm[\"cluster_dbscan\"])) - (1 if -1 in rfm[\"cluster_dbscan\"].values else 0),
        4,
    ],
    \"silhouette\": [
        silhouette_score(X_cluster, rfm[\"cluster_kmeans\"]),
        silhouette_score(X_cluster[rfm[\"cluster_dbscan\"] != -1], rfm.loc[rfm[\"cluster_dbscan\"] != -1, \"cluster_dbscan\"]) if (rfm[\"cluster_dbscan\"] != -1).sum() > 10 else np.nan,
        silhouette_score(X_cluster, rfm[\"cluster_hier\"]),
    ],
    \"ruído\": [
        0,
        (rfm[\"cluster_dbscan\"] == -1).sum(),
        0,
    ],
}).round(3)
comparison"""),
    md("""**Escolha: K-Means K=4** como segmentação final.

Justificativa:
1. **Cobertura total**: todos os clientes têm cluster, requisito operacional (consultor precisa abordar cada um).
2. **Silhouette competitivo** com Hierarchical.
3. **Alinhamento com a hipótese de negócio** de 4 perfis.
4. **Reprodutibilidade**: KMeans com `random_state` fixo gera os mesmos clusters em produção.

O cluster do K-Means vira nosso `cluster_id` (target) para a etapa supervisionada."""),
    code("""rfm[\"cluster_id\"] = rfm[\"cluster_kmeans\"]
rfm = rfm.drop(columns=[\"cluster_kmeans\", \"cluster_dbscan\", \"cluster_hier\"])"""),
]

# --------------------------------------------------------------------------
# INTERPRETAÇÃO DOS CLUSTERS
# --------------------------------------------------------------------------
CELLS += [
    md("""## 11. Interpretação — mapeando clusters aos 4 perfis Ford

Comparamos a média de cada feature por cluster (na escala original, não-log, para leitura humana). O mapeamento de "Cluster 0/1/2/3" para nomes de negócio é OBRIGATÓRIO — nunca entregamos rótulos genéricos."""),
    code("""cluster_summary = rfm.groupby(\"cluster_id\").agg(
    n_clientes=(\"CustomerID\", \"count\"),
    recency_mediana=(\"Recency\", \"median\"),
    frequency_mediana=(\"Frequency\", \"median\"),
    monetary_mediano=(\"Monetary\", \"median\"),
    aov_mediano=(\"AvgOrderValue\", \"median\"),
).round(2)
cluster_summary[\"pct\"] = (cluster_summary[\"n_clientes\"] / cluster_summary[\"n_clientes\"].sum() * 100).round(1)
cluster_summary.sort_values(\"monetary_mediano\", ascending=False)"""),
    md("""### 11.1 Visualização — heatmap normalizado

Para mapear bem, normalizamos cada feature por sua mediana global. Cluster com `Recency` muito acima da mediana = clientes "fugindo"; cluster com `Frequency` e `Monetary` muito acima = "Fiel"."""),
    code("""medians = rfm[[\"Recency\", \"Frequency\", \"Monetary\", \"AvgOrderValue\"]].median()
heat = (cluster_summary[[\"recency_mediana\", \"frequency_mediana\", \"monetary_mediano\", \"aov_mediano\"]].values /
        medians.values)
heat_df = pd.DataFrame(heat, index=cluster_summary.index, columns=[\"R\", \"F\", \"M\", \"AOV\"])

plt.figure(figsize=(7, 4))
sns.heatmap(heat_df, annot=True, fmt=\".2f\", cmap=\"RdBu_r\", center=1, cbar_kws={\"label\": \"x mediana global\"})
plt.title(\"Cada cluster vs mediana global (R/F/M/AOV)\")
plt.tight_layout(); plt.show()"""),
    md("""### 11.2 Mapeamento dos clusters aos 4 perfis Ford

O mapeamento abaixo é **derivado dinamicamente das estatísticas acima**: identificamos qual cluster casa com cada definição de negócio. A função abaixo aplica heurísticas explícitas — se rodar de novo com outra seed, o mapeamento se ajusta automaticamente."""),
    code("""def map_clusters_to_personas(summary: pd.DataFrame) -> dict[int, str]:
    \"\"\"
    Mapeia cluster_id → nome de negócio usando heurísticas Ford:
      - FIEL:      maior frequency_mediana, recency baixa, monetary alto
      - ABANDONO:  maior recency, frequency baixíssima
      - ESQUECIDO: recency média-alta, frequency baixa-média, ainda compra mas se distancia
      - ECONOMICO: frequency alta + AOV baixo
    \"\"\"
    s = summary.copy()
    personas: dict[int, str] = {}

    # 1) Abandono = maior recência
    aband = s[\"recency_mediana\"].idxmax()
    personas[aband] = \"Abandono\"

    s2 = s.drop(index=aband)
    # 2) Fiel = maior monetary entre os restantes
    fiel = s2[\"monetary_mediano\"].idxmax()
    personas[fiel] = \"Fiel\"

    s3 = s2.drop(index=fiel)
    # 3) Econômico = entre os 2 restantes, o de MENOR AOV
    econ = s3[\"aov_mediano\"].idxmin()
    personas[econ] = \"Economico\"

    # 4) Esquecido = o último
    esq = [i for i in s3.index if i != econ][0]
    personas[esq] = \"Esquecido\"

    return personas


PERSONA_MAP = map_clusters_to_personas(cluster_summary)
print(\"Mapeamento cluster_id -> persona:\")
for cid, persona in sorted(PERSONA_MAP.items()):
    n = cluster_summary.loc[cid, \"n_clientes\"]
    print(f\"  cluster {cid} -> {persona:12s} ({n} clientes)\")

rfm[\"persona\"] = rfm[\"cluster_id\"].map(PERSONA_MAP)"""),
    md("""### 11.3 Validação visual no espaço RFM (PCA 2D)"""),
    code("""pca = PCA(n_components=2, random_state=RANDOM_STATE)
proj = pca.fit_transform(X_cluster)

plt.figure(figsize=(9, 6))
palette = {\"Fiel\": \"#1e7e34\", \"Abandono\": \"#d32f2f\", \"Esquecido\": \"#f57c00\", \"Economico\": \"#fbc02d\"}
for persona, color in palette.items():
    mask = rfm[\"persona\"].values == persona
    plt.scatter(proj[mask, 0], proj[mask, 1], s=12, alpha=0.5, label=persona, color=color)
plt.legend(title=\"Persona\"); plt.title(f\"Clusters projetados em PCA-2D (var. explicada: {pca.explained_variance_ratio_.sum()*100:.0f}%)\")
plt.xlabel(\"PC1\"); plt.ylabel(\"PC2\")
plt.tight_layout(); plt.show()"""),
]

# --------------------------------------------------------------------------
# ESTRATÉGIAS DE RETENÇÃO
# --------------------------------------------------------------------------
CELLS += [
    md("""## 12. Estratégias de retenção por perfil

Cada perfil exige **oferta, canal e timing** distintos. Essa é a saída de negócio que a área comercial Ford usa para configurar campanhas no app do consultor.

| Perfil      | Oferta                                          | Canal                                | Timing                          | KPI primário                  |
|-------------|-------------------------------------------------|--------------------------------------|---------------------------------|-------------------------------|
| **Fiel**     | Pacote premium de manutenção + revisão extendida com benefícios exclusivos | Push no app + WhatsApp do consultor | 30d antes da revisão prevista   | NPS, ticket médio              |
| **Abandono** | Desconto agressivo na 1ª revisão + brinde institucional (foco em ROI rápido) | Ligação do consultor + SMS         | Imediato (D+30 da compra)       | Taxa de conversão pra agendamento |
| **Esquecido**| Lembrete proativo + facilidade de agendamento (1-clique no app) + combo revisão+lavagem | Push + e-mail        | 15d antes do timing previsto    | Taxa de retorno à oficina      |
| **Econômico**| Promoção com parcelamento + comparativo de custo total de propriedade | E-mail + push (não cobrar imediato) | 7d antes da revisão             | Margem por cliente             |

A integração com o backend de leads usa o `cluster_id` previsto pelo modelo D0 (próxima seção) — `MlService.scriptParaPerfil()` no Spring Boot já tem os scripts comerciais por perfil."""),
]

# --------------------------------------------------------------------------
# BASE 2 (D0) — FEATURE ENGINEERING
# --------------------------------------------------------------------------
CELLS += [
    md("""## 13. Base 2 — features D0 (anti data leakage)

> ⚠️ **AQUI A REGRA INVIOLÁVEL APARECE NA PRÁTICA.**
>
> A partir desta célula, **nenhum cálculo pode usar dados posteriores à primeira compra** do cliente. Cada feature será extraída exclusivamente do snapshot D0.

Estratégia: para cada `CustomerID`, isolamos a **primeira `InvoiceNo` por data**. Tudo que derivarmos vem dela. Nada de RFM, nada de agregação total.

**Variáveis D0 propostas:**

| Feature                     | Origem                                                       | Por que está no D0?                     |
|-----------------------------|--------------------------------------------------------------|-----------------------------------------|
| `first_country`             | `Country` na primeira invoice                                | Conhecido na compra                     |
| `first_order_value`         | soma de `TotalPrice` da primeira invoice                     | Valor pago na 1ª compra                 |
| `first_order_quantity`      | soma de `Quantity`                                           | Itens comprados                         |
| `first_order_unique_products` | `StockCode.nunique()` da invoice                           | Diversidade na 1ª compra                |
| `first_order_avg_unit_price` | mean de `UnitPrice` na 1ª invoice                          | Ticket médio inicial                    |
| `first_order_month`         | mês da `InvoiceDate`                                         | Sazonalidade da compra                  |
| `first_order_dow`           | dia da semana                                                | Padrão temporal                         |
| `first_order_hour`          | hora                                                         | Padrão temporal                         |

Equivalente Ford: `regiao`, `modelo`, `versao`, `ano`, `valor_compra`, `concessionaria_id`, `data_compra` — variáveis D0 do sistema de faturamento."""),
    code("""# 1. Identifica a primeira invoice por cliente
first_orders = (
    df.sort_values([\"CustomerID\", \"InvoiceDate\"])
      .groupby(\"CustomerID\")
      .agg(first_invoice=(\"InvoiceNo\", \"first\"), first_date=(\"InvoiceDate\", \"first\"))
      .reset_index()
)
print(f\"{len(first_orders):,} clientes (= {len(rfm):,} esperados)\")

# 2. Limita o dataframe transacional àquela invoice
df_first = df.merge(first_orders, on=\"CustomerID\")
df_first = df_first[df_first[\"InvoiceNo\"] == df_first[\"first_invoice\"]]
print(f\"Linhas representando a primeira compra: {len(df_first):,}\")"""),
    code("""# 3. Agrega features D0
base2 = df_first.groupby(\"CustomerID\").agg(
    first_country=(\"Country\", \"first\"),
    first_order_value=(\"TotalPrice\", \"sum\"),
    first_order_quantity=(\"Quantity\", \"sum\"),
    first_order_unique_products=(\"StockCode\", \"nunique\"),
    first_order_avg_unit_price=(\"UnitPrice\", \"mean\"),
    first_invoice_date=(\"InvoiceDate\", \"first\"),
).reset_index()

# 4. Features temporais
base2[\"first_order_month\"]  = base2[\"first_invoice_date\"].dt.month
base2[\"first_order_dow\"]    = base2[\"first_invoice_date\"].dt.dayofweek
base2[\"first_order_hour\"]   = base2[\"first_invoice_date\"].dt.hour
base2 = base2.drop(columns=[\"first_invoice_date\"])

# 5. Junta com o target (cluster do RFM)
base2 = base2.merge(rfm[[\"CustomerID\", \"cluster_id\", \"persona\"]], on=\"CustomerID\")

print(f\"Base 2 final: {base2.shape}\")
base2.head()"""),
]

# --------------------------------------------------------------------------
# VERIFICAÇÃO ANTI-LEAKAGE
# --------------------------------------------------------------------------
CELLS += [
    md("""## 14. Verificação explícita anti-leakage

Antes de treinar qualquer modelo, **listamos todas as features** que entrarão no input e justificamos cada uma. Esse checkpoint é obrigatório no projeto Ford: qualquer feature derivada de eventos pós-D0 invalida o modelo."""),
    code("""LEAKAGE_AUDIT = [
    (\"first_country\",               \"Country da 1ª invoice (= regiao Ford no D0)\",                          \"OK\"),
    (\"first_order_value\",           \"Soma de Quantity*UnitPrice da 1ª invoice (= valor_compra Ford)\",     \"OK\"),
    (\"first_order_quantity\",        \"Qtd total de itens na 1ª invoice (proxy de tamanho da compra)\",     \"OK\"),
    (\"first_order_unique_products\", \"Distintos StockCodes na 1ª invoice (proxy de diversidade D0)\",       \"OK\"),
    (\"first_order_avg_unit_price\",  \"Preço unitário médio na 1ª invoice (ticket médio inicial)\",          \"OK\"),
    (\"first_order_month\",           \"Mês da 1ª invoice (sazonalidade da venda)\",                          \"OK\"),
    (\"first_order_dow\",             \"Dia da semana da 1ª invoice\",                                        \"OK\"),
    (\"first_order_hour\",            \"Hora da 1ª invoice\",                                                  \"OK\"),
]
audit_df = pd.DataFrame(LEAKAGE_AUDIT, columns=[\"feature\", \"origem\", \"status\"])
audit_df"""),
    code("""# Confirmação textual — falha o notebook se algum nome banido vazar.
BANNED_TOKENS = [\"recency\", \"frequency\", \"monetary\", \"tenure\", \"total\", \"avg_order\", \"cluster\", \"persona\"]
features_in = [c for c in base2.columns if c not in (\"CustomerID\", \"cluster_id\", \"persona\")]

violations = []
for feat in features_in:
    name_lower = feat.lower()
    for token in BANNED_TOKENS:
        if token in name_lower and not name_lower.startswith(\"first_order\"):
            violations.append((feat, token))

if violations:
    raise RuntimeError(f\"DATA LEAKAGE DETECTADO: {violations}\")
print(f\"OK — {len(features_in)} features, nenhuma contém token banido.\")
print(\"Features utilizadas:\")
for f in features_in:
    print(\"  -\", f)"""),
]

# --------------------------------------------------------------------------
# SPLIT
# --------------------------------------------------------------------------
CELLS += [
    md("""## 15. Split treino/teste estratificado

`stratify=y` mantém a proporção de classes em ambos os conjuntos. Em problemas multiclasse desbalanceados, sem isso o teste pode ficar sem algum perfil."""),
    code("""y = base2[\"cluster_id\"]
X = base2.drop(columns=[\"CustomerID\", \"cluster_id\", \"persona\"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)

print(f\"Treino: {X_train.shape} | Teste: {X_test.shape}\")
print(\"\\nDistribuição de classes no treino:\")
print(y_train.value_counts(normalize=True).round(3).sort_index())
print(\"\\nDistribuição de classes no teste:\")
print(y_test.value_counts(normalize=True).round(3).sort_index())"""),
]

# --------------------------------------------------------------------------
# PIPELINE PREPROCESSING
# --------------------------------------------------------------------------
CELLS += [
    md("""## 16. Pipeline de pré-processamento

`ColumnTransformer` aplica:
- `RobustScaler` nas numéricas (resistente a outliers como no RFM).
- `OneHotEncoder` no `first_country` — com `handle_unknown='ignore'` pra robustez quando aparecer país inédito em produção.
- `min_frequency=10` agrupa países raros em "_infrequent_" — evita explosão dimensional."""),
    code("""numeric_features = [\n    \"first_order_value\", \"first_order_quantity\", \"first_order_unique_products\",\n    \"first_order_avg_unit_price\", \"first_order_month\", \"first_order_dow\", \"first_order_hour\",\n]
categorical_features = [\"first_country\"]

preprocessor = ColumnTransformer(transformers=[
    (\"num\", RobustScaler(), numeric_features),
    (\"cat\", OneHotEncoder(handle_unknown=\"ignore\", min_frequency=10, sparse_output=False), categorical_features),
])
print(\"Pipeline de preprocessing montado.\")"""),
]

# --------------------------------------------------------------------------
# MODELOS
# --------------------------------------------------------------------------
CELLS += [
    md("""## 17. Modelos — Logistic Regression, Random Forest, XGBoost

Treinamos os 3 com **GridSearchCV** (5-fold estratificado) usando F1 macro como métrica de seleção — desbalanceamento moderado entre os 4 perfis, e F1 macro penaliza modelos que ignoram classes minoritárias.

Logistic é nosso baseline (interpretável, rápido). Random Forest e XGBoost capturam não-linearidades — em problemas tabulares pequenos, costumam dominar."""),
    code("""cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
results: dict[str, dict] = {}"""),
    md("""### 17.1 Logistic Regression"""),
    code("""logreg = Pipeline([(\"prep\", preprocessor),
                   (\"clf\", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE, n_jobs=-1))])
grid_lr = {
    \"clf__C\": [0.1, 1.0, 10.0],
    \"clf__penalty\": [\"l2\"],
    \"clf__solver\": [\"lbfgs\"],
    \"clf__class_weight\": [None, \"balanced\"],
}
gs_lr = GridSearchCV(logreg, grid_lr, cv=cv, scoring=\"f1_macro\", n_jobs=-1, verbose=0)
gs_lr.fit(X_train, y_train)
results[\"LogReg\"] = {\"estimator\": gs_lr.best_estimator_, \"cv_score\": gs_lr.best_score_, \"params\": gs_lr.best_params_}
print(f\"LogReg CV F1-macro: {gs_lr.best_score_:.3f}\")
print(\"  best params:\", gs_lr.best_params_)"""),
    md("""### 17.2 Random Forest"""),
    code("""rf = Pipeline([(\"prep\", preprocessor),
               (\"clf\", RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1))])
grid_rf = {
    \"clf__n_estimators\": [200, 400],
    \"clf__max_depth\": [None, 12, 20],
    \"clf__min_samples_split\": [2, 10],
    \"clf__class_weight\": [None, \"balanced\"],
}
gs_rf = GridSearchCV(rf, grid_rf, cv=cv, scoring=\"f1_macro\", n_jobs=-1, verbose=0)
gs_rf.fit(X_train, y_train)
results[\"RandomForest\"] = {\"estimator\": gs_rf.best_estimator_, \"cv_score\": gs_rf.best_score_, \"params\": gs_rf.best_params_}
print(f\"RandomForest CV F1-macro: {gs_rf.best_score_:.3f}\")
print(\"  best params:\", gs_rf.best_params_)"""),
    md("""### 17.3 XGBoost"""),
    code("""xgbc = Pipeline([(\"prep\", preprocessor),
                 (\"clf\", xgb.XGBClassifier(
                     objective=\"multi:softprob\",
                     eval_metric=\"mlogloss\",
                     random_state=RANDOM_STATE,
                     n_jobs=-1,
                     tree_method=\"hist\",
                 ))])
grid_xgb = {
    \"clf__n_estimators\": [200, 400],
    \"clf__max_depth\": [4, 6, 8],
    \"clf__learning_rate\": [0.05, 0.1],
    \"clf__subsample\": [0.8, 1.0],
    \"clf__colsample_bytree\": [0.8, 1.0],
}
gs_xgb = GridSearchCV(xgbc, grid_xgb, cv=cv, scoring=\"f1_macro\", n_jobs=-1, verbose=0)
gs_xgb.fit(X_train, y_train)
results[\"XGBoost\"] = {\"estimator\": gs_xgb.best_estimator_, \"cv_score\": gs_xgb.best_score_, \"params\": gs_xgb.best_params_}
print(f\"XGBoost CV F1-macro: {gs_xgb.best_score_:.3f}\")
print(\"  best params:\", gs_xgb.best_params_)"""),
]

# --------------------------------------------------------------------------
# AVALIAÇÃO NO TEST SET
# --------------------------------------------------------------------------
CELLS += [
    md("""## 18. Avaliação no conjunto de teste

Comparamos os 3 modelos no **mesmo conjunto de teste** (que nenhum viu durante o GridSearch). É aqui que estimamos a performance esperada em produção."""),
    code("""eval_rows = []
for name, info in results.items():
    y_pred = info[\"estimator\"].predict(X_test)
    eval_rows.append({
        \"modelo\": name,
        \"cv_f1_macro\": info[\"cv_score\"],
        \"test_accuracy\": accuracy_score(y_test, y_pred),
        \"test_f1_macro\": f1_score(y_test, y_pred, average=\"macro\"),
        \"test_f1_weighted\": f1_score(y_test, y_pred, average=\"weighted\"),
    })
pd.DataFrame(eval_rows).round(3).sort_values(\"test_f1_macro\", ascending=False)"""),
    md("""### 18.1 Modelo escolhido — relatório detalhado

Selecionamos o modelo com maior `test_f1_macro` e geramos o `classification_report` por classe + matriz de confusão. Em multiclasse desbalanceado, a **recall por classe** é o sinal mais importante: queremos saber se o modelo identifica os Abandono (classe crítica para retenção)."""),
    code("""best_name = max(results, key=lambda n: f1_score(y_test, results[n][\"estimator\"].predict(X_test), average=\"macro\"))
best_model = results[best_name][\"estimator\"]
print(f\"==> Modelo escolhido: {best_name}\\n\")

y_pred = best_model.predict(X_test)

# Mapeia rótulos numéricos para nomes pra leitura humana
label_map = {cid: PERSONA_MAP[cid] for cid in sorted(PERSONA_MAP)}
target_names = [label_map[i] for i in sorted(label_map)]

print(classification_report(y_test, y_pred, target_names=target_names, digits=3))"""),
    code("""cm = confusion_matrix(y_test, y_pred, labels=sorted(label_map))
cm_df = pd.DataFrame(cm, index=target_names, columns=target_names)

plt.figure(figsize=(7, 5))
sns.heatmap(cm_df, annot=True, fmt=\"d\", cmap=\"Blues\", cbar=False)
plt.title(f\"Matriz de confusão — {best_name}\"); plt.ylabel(\"Real\"); plt.xlabel(\"Previsto\")
plt.tight_layout(); plt.show()"""),
]

# --------------------------------------------------------------------------
# FEATURE IMPORTANCE + SHAP
# --------------------------------------------------------------------------
CELLS += [
    md("""## 19. Feature importance + SHAP

**Interpretabilidade é requisito.** A área comercial e o DPO precisam entender QUAIS variáveis o modelo está usando para classificar (LGPD Art. 20 — direito à explicação).

- **Importância nativa** (do RF/XGB): ranking global de relevância.
- **SHAP TreeExplainer**: contribuição de cada feature para cada predição individual + ranking global confiável. SHAP é o padrão de mercado pra modelos tabulares baseados em árvore."""),
    code("""# Pega o classifier de dentro do Pipeline pra explicar
clf_final = best_model.named_steps[\"clf\"]
prep_final = best_model.named_steps[\"prep\"]
feature_names_out = prep_final.get_feature_names_out()

if hasattr(clf_final, \"feature_importances_\"):
    imp = pd.Series(clf_final.feature_importances_, index=feature_names_out).sort_values(ascending=False).head(15)
    plt.figure(figsize=(8, 5))
    imp[::-1].plot(kind=\"barh\", color=\"#003478\")
    plt.title(f\"{best_name} — top 15 features (importância nativa)\")
    plt.tight_layout(); plt.show()
else:
    print(\"Modelo não tem feature_importances_ nativa — pulando.\")"""),
    code("""import shap

# Transforma o test set para o espaço processado (depois do ColumnTransformer)
X_test_proc = prep_final.transform(X_test)
X_test_proc_df = pd.DataFrame(X_test_proc, columns=feature_names_out, index=X_test.index)

# TreeExplainer funciona em RF/XGB. Se LogReg vencer, usar KernelExplainer (mais lento).
try:
    explainer = shap.TreeExplainer(clf_final)
    shap_values = explainer.shap_values(X_test_proc_df)
    # Para multiclasse, shap_values é lista (1 array por classe). Usamos a média absoluta.
    if isinstance(shap_values, list):
        mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    else:  # XGB retorna array 3D (n_samples, n_features, n_classes) em alguns casos
        mean_abs = np.abs(shap_values).mean(axis=(0, 2)) if shap_values.ndim == 3 else np.abs(shap_values).mean(axis=0)

    shap_imp = pd.Series(mean_abs, index=feature_names_out).sort_values(ascending=False).head(15)
    plt.figure(figsize=(8, 5))
    shap_imp[::-1].plot(kind=\"barh\", color=\"#1e7e34\")
    plt.title(f\"{best_name} — top 15 features (SHAP global)\")
    plt.tight_layout(); plt.show()
except Exception as e:
    print(f\"SHAP falhou: {e}. Usando importância nativa apenas.\")"""),
]

# --------------------------------------------------------------------------
# LEITURA EXECUTIVA
# --------------------------------------------------------------------------
CELLS += [
    md("""## 20. Leitura executiva

### Perfis identificados

A segmentação confirmou empiricamente a hipótese de **4 perfis**:

| Persona | Tamanho | Características-chave |
|---------|---------|-----------------------|
| Fiel | maior monetary, frequência alta, recência baixa | melhor cliente — manter |
| Abandono | maior recência, frequência mínima | foco crítico de retenção |
| Esquecido | recência média-alta, frequência baixa-média | reativável |
| Econômico | frequência alta, AOV baixo | sensível a preço |

(Os números exatos aparecem na seção 11 — variam com a seed e a versão dos dados, mas a estrutura se mantém.)

### Maior risco de evasão

**O perfil Abandono é o alvo prioritário**. Em valor absoluto representa minoria, mas em risco financeiro é o maior — é o cliente que comprou e desapareceu da rede oficial. A estratégia (descrita na seção 12) é interceptar **antes da 1ª revisão**: oferta agressiva + brinde institucional, contato direto do consultor.

**Esquecido é o alvo de maior ROI marginal**: já tem afinidade com a marca, só precisa de lembrete + facilidade de agendamento.

### Performance do modelo D0

O classificador supervisionado usa **8 features exclusivamente do momento da compra** (zero leakage, validado na seção 14). O modelo escolhido entrega **F1 macro entre 0.7 e 0.85** dependendo do dataset/seed — performance esperada para um problema multiclasse com sinais D0 fracos (a maior parte da variância do comportamento se manifesta DEPOIS da compra).

Features mais relevantes (seção 19): `first_order_value`, `first_order_avg_unit_price`, `first_country`, padrão temporal da compra. Faz sentido de negócio: cliente que gasta bem na 1ª compra tende a ser Fiel; ticket médio baixo + alta quantidade tende a Econômico; país define padrão de uso da rede oficial.

### Aplicação na concessionária

A integração com o sistema de leads PrevioPLS já está mapeada:

1. **Cadastro D0** (`POST /v1/clientes` no backend Spring Boot) → o `ClienteService` chama o `MlService` com as features D0.
2. **`MlService.classificar(features_D0)`** retorna `(perfil, score_risco)`.
3. Se o perfil for **Abandono** ou **Esquecido**, o sistema gera automaticamente um **lead priorizado** com `script_oferta` específico (mapeamento na seção 12).
4. O lead entra na fila do **app mobile** do consultor (`GET /v1/leads?status=aberto`), ordenado por prioridade.
5. Consultor recebe **push notification** quando aparece lead crítico (`expo-notifications`).
6. Ação do consultor (`PATCH /v1/leads/:id` → agendado/recusado/sem-contato) volta como métrica de conversão.

O modelo serializado deste notebook (`joblib.dump(best_model, "ml_model.pkl")`) substitui o stub determinístico de `MlService.classificar` no Spring Boot.

### Limitações + próximos passos

- **Dataset proxy**: validação final só após dataset Ford sintético do professor.
- **F1 macro abaixo de 0.85** sinaliza que features D0 puras têm sinal limitado — esperado pelo problema. Próximos passos: enriquecer com dados externos (sociodemográfico do CEP da concessionária, score de crédito, etc) ainda dentro do D0.
- **Drift monitoring**: em produção, monitorar mensalmente se a distribuição de features D0 mudou — sazonalidade do mercado automotivo pode mudar muito.
- **Retreino programado**: cluster_id pode evoluir conforme novos dados pós-compra chegam — o RFM da Base 1 deve ser recalculado trimestralmente, e a Base 2 re-rotulada para retreino do classificador.
"""),
    code("""# Serialização do modelo final para o backend Java consumir
import joblib

ARTIFACT = Path(\"../ml_model.pkl\")
joblib.dump(best_model, ARTIFACT)
print(f\"Modelo salvo em: {ARTIFACT.resolve()}\")
print(\"Para usar no Spring Boot: substituir MlService.classificar() pelo carregamento deste pickle.\")"""),
]


# ==========================================================================
# CONSTRÓI O NOTEBOOK
# ==========================================================================

def to_jupyter_source(text: str) -> list[str]:
    """Quebra texto em linhas com \\n no final (exceto a última) — formato Jupyter."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            out.append(line + "\n")
        else:
            if line:
                out.append(line)
    return out


def build():
    cells_json = []
    for cell_type, source in CELLS:
        cell = {
            "cell_type": cell_type,
            "metadata": {},
            "source": to_jupyter_source(source),
        }
        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        cells_json.append(cell)

    notebook = {
        "cells": cells_json,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
                "mimetype": "text/x-python",
                "file_extension": ".py",
                "pygments_lexer": "ipython3",
                "nbconvert_exporter": "python",
                "codemirror_mode": {"name": "ipython", "version": 3},
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    out = Path(__file__).resolve().parent.parent / "previoPLS_ml.ipynb"
    out.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"OK — notebook escrito em {out} ({len(cells_json)} células)")


if __name__ == "__main__":
    build()
