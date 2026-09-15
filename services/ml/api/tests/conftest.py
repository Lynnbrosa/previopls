import os
from pathlib import Path

import joblib
import pytest


@pytest.fixture(scope="session")
def model_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Treina o pipeline sintético padrão uma vez por sessão e devolve o caminho do pkl."""
    from app.build_default_model import _synthetic_dataset, build_pipeline

    df = _synthetic_dataset(n=800)
    features = ["regiao", "modelo", "ano", "valor_compra", "concessionaria_id"]
    pipeline = build_pipeline()
    pipeline.fit(df[features], df["perfil"])

    path = tmp_path_factory.mktemp("models") / "ml_model.pkl"
    joblib.dump(pipeline, path)
    return path


@pytest.fixture()
def client(model_path: Path, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("ML_MODEL_PATH", str(model_path))
    from app.main import app

    with TestClient(app) as c:
        yield c
