"""
Gera um ml_model.pkl padrão para o ml-api funcionar fora da caixa em desenvolvimento.

O modelo real deve vir do notebook em services/ml/notebook/previoPLS_ml.ipynb,
treinado sobre o dataset Online Retail (proxy metodológico) ou, em produção,
sobre o dataset Ford via scripts/retrain-with-ford-data.sh.

O pipeline aqui produzido tem o mesmo contrato do que o notebook exporta:
- input: regiao, modelo, ano, valor_compra, concessionaria_id (D0 puro)
- output: probabilidades sobre {FIEL, ABANDONO, ESQUECIDO, ECONOMICO}
- método: ColumnTransformer (OneHot + passthrough) seguido de LogisticRegression

A amostra sintética é determinística (random_state=42) e respeita a US02
(nenhuma variável pós-venda no input).
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RNG = np.random.default_rng(42)

REGIOES = ("SP", "RJ", "MG", "RS", "PR", "BA", "PE", "DF")
MODELOS = ("Ranger", "Transit", "Maverick", "F-150", "Bronco Sport", "Mustang", "Territory")
CONCESSIONARIAS = tuple(f"FORD-{r}-{i:03d}" for r in REGIOES for i in range(1, 6))
PERFIS = ("FIEL", "ABANDONO", "ESQUECIDO", "ECONOMICO")


def _synthetic_dataset(n: int = 4000) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "regiao": RNG.choice(REGIOES, n),
            "modelo": RNG.choice(MODELOS, n),
            "ano": RNG.integers(2018, 2027, n),
            "valor_compra": RNG.normal(180_000, 50_000, n).clip(60_000, 600_000),
            "concessionaria_id": RNG.choice(CONCESSIONARIAS, n),
        }
    )

    valor_norm = (df["valor_compra"] - df["valor_compra"].mean()) / df["valor_compra"].std()
    ano_recent = (df["ano"] - 2018) / 9

    score_fiel = valor_norm * 0.6 + ano_recent * 0.4
    score_econ = -valor_norm * 0.7 + RNG.normal(0, 0.5, n)
    score_aband = -ano_recent * 0.5 + RNG.normal(0, 0.6, n)
    score_esqu = RNG.normal(0, 0.6, n) - valor_norm * 0.2

    scores = np.column_stack([score_fiel, score_aband, score_esqu, score_econ])
    df["perfil"] = np.array(PERFIS)[np.argmax(scores, axis=1)]
    return df


def build_pipeline() -> Pipeline:
    categorical = ["regiao", "modelo", "concessionaria_id"]
    numeric = ["ano", "valor_compra"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
            ("num", StandardScaler(), numeric),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    classifier = LogisticRegression(
        max_iter=2000,
        random_state=42,
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])


def main() -> None:
    df = _synthetic_dataset()
    feature_columns = ["regiao", "modelo", "ano", "valor_compra", "concessionaria_id"]
    X = df[feature_columns]
    y = df["perfil"]

    pipeline = build_pipeline()
    pipeline.fit(X, y)

    out_dir = Path(__file__).resolve().parent.parent / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ml_model.pkl"
    joblib.dump(pipeline, out_path)
    print(f"ml_model.pkl gravado em {out_path}")


if __name__ == "__main__":
    main()
