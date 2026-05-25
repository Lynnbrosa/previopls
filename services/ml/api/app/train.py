"""
Retreina o pipeline D0 a partir de um dataset Ford real.

Espera um arquivo Excel no formato vin_share_Desafio_02.xlsx (mesmo schema
usado pelo scripts/build-seed/build_seed.py). O modelo gerado substitui o
ml_model.pkl atual em services/ml/api/models/.

Este script existe para o caso em que o dataset Ford estiver disponível.
Em desenvolvimento normal, use o notebook em services/ml/notebook/ com
o proxy Online Retail.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

from app.build_default_model import build_pipeline
from app.predictor import _check_anti_leakage  # mesma regra do server-side

EXPECTED_COLUMNS = ("VIN_Hash", "ModelName", "ModelYear", "SalesDate", "DealerCode")
REGIAO_PADRAO = "SP"


def load_ford_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"dataset Ford não tem colunas esperadas: {missing}")

    valor_compra = df.get("InvoiceAmount", pd.Series([180_000.0] * len(df)))
    regiao = df.get("Regiao", pd.Series([REGIAO_PADRAO] * len(df)))

    features = pd.DataFrame(
        {
            "regiao": regiao.fillna(REGIAO_PADRAO).astype(str),
            "modelo": df["ModelName"].astype(str),
            "ano": df["ModelYear"].astype(int),
            "valor_compra": valor_compra.astype(float),
            "concessionaria_id": df["DealerCode"].apply(lambda d: f"FORD-{d}").astype(str),
        }
    )
    features["perfil"] = df.get("Perfil", _derive_perfil(features))
    return features


def _derive_perfil(features: pd.DataFrame) -> pd.Series:
    raise SystemExit(
        "A coluna Perfil não veio rotulada no dataset Ford. "
        "Use o notebook completo (services/ml/notebook/) que faz a segmentação "
        "RFM antes da classificação D0."
    )


def train(dataset_path: Path, output_path: Path) -> None:
    df = load_ford_dataset(dataset_path)
    X = df[["regiao", "modelo", "ano", "valor_compra", "concessionaria_id"]]
    y = df["perfil"].astype(str)

    pipeline = build_pipeline()
    pipeline.fit(X, y)

    _check_anti_leakage(tuple(str(c) for c in pipeline.feature_names_in_))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)
    print(f"ml_model.pkl gravado em {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Retreina o modelo D0 com dados Ford")
    parser.add_argument("dataset", type=Path, help="caminho do vin_share_Desafio_02.xlsx")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "models" / "ml_model.pkl",
    )
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"dataset não encontrado: {args.dataset}")

    train(args.dataset, args.output)


if __name__ == "__main__":
    main()
