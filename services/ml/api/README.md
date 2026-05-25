# ml-api

Servidor de inferência D0 do PrevioPLS. Carrega o `ml_model.pkl` exportado do notebook em [`services/ml/notebook/`](../notebook/) e expõe `POST /predict` para o Core consumir via REST interno.

## Contrato

`POST /predict`

```json
{
  "regiao": "SP",
  "modelo": "Ranger",
  "ano": 2026,
  "valor_compra": "250000.00",
  "concessionaria_id": "FORD-SP-001"
}
```

Resposta:

```json
{
  "perfil": "ABANDONO",
  "score": 0.83,
  "latency_ms": 7
}
```

Campos:

- `perfil`: um de `FIEL`, `ABANDONO`, `ESQUECIDO`, `ECONOMICO`.
- `score`: probabilidade da classe predita (faixa 0.0 a 1.0).
- `latency_ms`: tempo de inferência medido no servidor.

A regra de produto US02 restringe o input a features D0 puras. Nenhuma variável pós-venda entra no contrato.

Outros endpoints úteis:

- `GET /health`: `{status, model_loaded, model_version}`.
- `GET /version`: identifica nome, versão da API e versão do modelo carregado.

## Validação anti-leakage no boot

O `load_model` em [`app/predictor.py`](app/predictor.py) verifica que o `feature_names_in_` do pipeline carregado não contém nenhum dos tokens banidos `recency`, `frequency`, `monetary`, `tenure` como substring, nem começa com os prefixos RFM `r_`, `f_`, `m_`. Se aparecer, o boot lança `RuntimeError` e o container morre. Também valida que `classes_` está dentro do contrato `{FIEL, ABANDONO, ESQUECIDO, ECONOMICO}`.

Essa é a contraparte server-side da Seção 14 do notebook, ver [`services/ml/notebook/previoPLS_ml.ipynb`](../notebook/previoPLS_ml.ipynb).

## Como o modelo entra aqui

Em ordem de prioridade:

1. **Notebook treinado com Online Retail (proxy)**. Após rodar o notebook, copie `services/ml/notebook/output/ml_model.pkl` (ou o caminho onde o `joblib.dump` ficou) para `services/ml/api/models/ml_model.pkl`.
2. **Notebook treinado com dataset Ford real** (recomendado para piloto). Use o script [`scripts/retrain-with-ford-data.sh`](../../../scripts/retrain-with-ford-data.sh).
3. **Modelo padrão sintético**. Se `models/ml_model.pkl` não existir no momento do build, o `Dockerfile` executa [`app/build_default_model.py`](app/build_default_model.py), que gera um pipeline `OneHotEncoder + StandardScaler + LogisticRegression` treinado em dados sintéticos determinísticos. Útil para o stack do compose funcionar fora da caixa, não para avaliar performance.

O `Dockerfile` segue essa ordem na build. O `predictor` valida o pkl carregado antes de servir o primeiro request.

## Latência observada

O alvo de produto é p95 menor que 500ms. O modelo `LogisticRegression` do build padrão fica em ordem de unidades de milissegundo em hardware comum. Pipelines mais pesados (XGBoost, Random Forest) ainda ficam folgados dentro do envelope para o tamanho de payload do D0.

Para medir localmente:

```bash
# com o ml-api subido pelo compose
ab -n 1000 -c 10 -p body.json -T application/json http://localhost:8000/predict
```

Onde `body.json` contém o payload mostrado acima.

## Variáveis de ambiente

| Var              | Default                         | Descrição                                      |
|------------------|----------------------------------|--------------------------------------------------|
| `ML_MODEL_PATH`  | `/app/models/ml_model.pkl`       | Caminho absoluto do pickle a carregar.           |
| `LOG_LEVEL`      | `INFO`                           | DEBUG, INFO, WARNING, ERROR.                      |

## Como rodar isolado (sem compose)

```bash
cd services/ml/api
pip install -r requirements.txt
python -m app.build_default_model        # opcional, gera ml_model.pkl
uvicorn app.main:app --reload --port 8000
```

Com isso, o `POST /predict` aceita conexões em `http://localhost:8000/predict`.

## Como o Core consome

`MlService` ([`services/core/src/main/java/com/previopls/service/MlService.java`](../../core/src/main/java/com/previopls/service/MlService.java)) faz a chamada REST com `RestClient` do Spring Boot 3.3. Timeout de 2 segundos. Em caso de erro de rede ou status diferente de 2xx, faz fallback para perfil `ESQUECIDO` com score `0.5`, loga warning e segue. A requisição principal não falha por indisponibilidade do ml-api.

URL configurável via `ML_API_URL` no ambiente do Core (default `http://ml-api:8000`).
