# Render · ml-api

Servidor de inferência scikit-learn do PrevioPLS. Recebe features D0 e devolve perfil + score.

## Setup no painel da Render

1. **New** → **Web Service**.
2. **Connect a repository**: `Lynnbrosa/previopls`.
3. **Name**: `previopls-ml-api`.
4. **Root Directory**: `services/ml/api`.
5. **Runtime**: `Docker`. Dockerfile do próprio diretório.
6. **Plan**: Free.
7. **Health Check Path**: `/health`.

## Variáveis de ambiente

| Var              | Valor                                  |
|------------------|-----------------------------------------|
| `ML_MODEL_PATH`  | `/app/models/ml_model.pkl`              |
| `LOG_LEVEL`      | `INFO`                                  |

O Dockerfile gera um `ml_model.pkl` padrão sintético durante o build (via `app.build_default_model`). Para subir o modelo real treinado no notebook, duas opções:

1. **Build customizado**: copiar o `ml_model.pkl` para `services/ml/api/models/` antes do push. O `COPY models/ ./models/` do Dockerfile o pega automaticamente. Funciona, mas commita um binário no Git.
2. **Volume montado via Render Disk** (recomendado): criar um disco persistente, fazer upload do `ml_model.pkl` via shell do Render e mountar em `/app/models/`. Atualizar o modelo sem rebuild.

A opção 2 não tem custo adicional no plano free desde que o disco fique abaixo de 1 GB.

## Domínio público

Nenhum. O ml-api é privado, chamado apenas pelo Core via rede interna do Render.

## Anti-leakage no boot

O `predictor.load_model` lança `RuntimeError` se o pipeline tiver features D0-banidas (`recency`, `frequency`, `monetary`, `tenure`, `r_`, `f_`, `m_`) ou classes fora do contrato `{FIEL, ABANDONO, ESQUECIDO, ECONOMICO}`. Se o boot falhar, verifique o pkl no disco contra o checksum gerado pelo notebook.

## Limitações conhecidas

- Plano free tem 512 MB de RAM. Para sklearn + numpy + pandas, é apertado. Modelos grandes (XGBoost com muitas árvores) podem não caber. LogisticRegression e Random Forest leves ficam folgados.
- Cold start de FastAPI é rápido (segundos). Mesmo após hibernação, o ml-api volta a responder bem antes do JVM do Core.
