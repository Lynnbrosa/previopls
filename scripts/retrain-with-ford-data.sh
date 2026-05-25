#!/usr/bin/env bash
#
# Retreina o modelo D0 do PrevioPLS com o dataset Ford real.
#
# Pré-requisitos:
# - Python 3.12 com as dependências de services/ml/api/requirements.txt instaladas
# - Arquivo vin_share_Desafio_02.xlsx fornecido pelo canal oficial Ford
#   (não versionado neste repositório, ver .gitignore)
#
# Uso:
#   scripts/retrain-with-ford-data.sh /caminho/para/vin_share_Desafio_02.xlsx
#
# O script:
#   1) valida o caminho do dataset;
#   2) treina um pipeline D0 puro (US02) sobre o dataset Ford;
#   3) grava services/ml/api/models/ml_model.pkl, sobrescrevendo o anterior;
#   4) reinicia o container ml-api se o compose estiver rodando.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "uso: $0 /caminho/para/vin_share_Desafio_02.xlsx" >&2
  exit 1
fi

DATASET="$1"
if [[ ! -f "$DATASET" ]]; then
  echo "dataset não encontrado: $DATASET" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ML_API_DIR="$REPO_ROOT/services/ml/api"
OUTPUT="$ML_API_DIR/models/ml_model.pkl"

echo "Treinando modelo D0 a partir de: $DATASET"
echo "Output: $OUTPUT"

cd "$ML_API_DIR"
python -m app.train "$DATASET" --output "$OUTPUT"

echo
echo "Modelo regerado em $OUTPUT"
echo "Hash:"
sha256sum "$OUTPUT" | cut -c1-12

COMPOSE_FILE="$REPO_ROOT/infra/docker-compose.yml"
if command -v docker >/dev/null 2>&1 && [[ -f "$COMPOSE_FILE" ]]; then
  if docker compose -f "$COMPOSE_FILE" ps --services 2>/dev/null | grep -q "^ml-api$"; then
    echo
    echo "Reiniciando container ml-api para recarregar o pkl..."
    docker compose -f "$COMPOSE_FILE" restart ml-api || true
  fi
fi
