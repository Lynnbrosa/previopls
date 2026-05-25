from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.logging import get_logger

log = get_logger("ml-api.predictor")

BANNED_TOKENS = ("recency", "frequency", "monetary", "tenure")
BANNED_PREFIXES = ("r_", "f_", "m_")

ALLOWED_PERFIS = ("FIEL", "ABANDONO", "ESQUECIDO", "ECONOMICO")
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "ml_model.pkl"


@dataclass(frozen=True)
class LoadedModel:
    pipeline: Any
    feature_names: tuple[str, ...]
    classes: tuple[str, ...]
    version: str


def _model_version(path: Path) -> str:
    if not path.exists():
        return "unknown"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    return f"sha256:{digest}"


def _check_anti_leakage(feature_names: tuple[str, ...]) -> None:
    leaked = [
        name
        for name in feature_names
        if any(tok in name.lower() for tok in BANNED_TOKENS)
        or any(name.lower().startswith(prefix) for prefix in BANNED_PREFIXES)
    ]
    if leaked:
        raise RuntimeError(
            "Pipeline carrega features pós-venda banidas pela US02: " + ", ".join(leaked)
        )


def _validate_classes(classes: tuple[str, ...]) -> None:
    unknown = [c for c in classes if c not in ALLOWED_PERFIS]
    if unknown:
        raise RuntimeError(
            "Pipeline emite classes fora do contrato PrevioPLS: " + ", ".join(unknown)
        )


def load_model(path: Path | None = None) -> LoadedModel:
    target = path or Path(os.getenv("ML_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    if not target.exists():
        raise FileNotFoundError(f"ml_model.pkl não encontrado em {target}")

    pipeline = joblib.load(target)

    feature_names = _extract_feature_names(pipeline)
    classes = tuple(str(c) for c in getattr(pipeline, "classes_", ()))

    _check_anti_leakage(feature_names)
    _validate_classes(classes)

    version = _model_version(target)
    log.info(
        "model_loaded",
        path=str(target),
        feature_names=list(feature_names),
        classes=list(classes),
        version=version,
    )
    return LoadedModel(pipeline=pipeline, feature_names=feature_names, classes=classes, version=version)


def _extract_feature_names(pipeline: Any) -> tuple[str, ...]:
    names = getattr(pipeline, "feature_names_in_", None)
    if names is not None:
        return tuple(str(n) for n in names)
    if hasattr(pipeline, "named_steps"):
        for step in pipeline.named_steps.values():
            names = getattr(step, "feature_names_in_", None)
            if names is not None:
                return tuple(str(n) for n in names)
    raise RuntimeError("Pipeline não expõe feature_names_in_, impossível validar anti-leakage")


def to_features_frame(payload: dict[str, Any], expected: tuple[str, ...]) -> pd.DataFrame:
    row = {
        "regiao": str(payload["regiao"]),
        "modelo": str(payload["modelo"]),
        "ano": int(payload["ano"]),
        "valor_compra": float(_as_decimal(payload["valor_compra"])),
        "concessionaria_id": str(payload["concessionaria_id"]),
    }
    frame = pd.DataFrame([row])
    missing = [name for name in expected if name not in frame.columns]
    if missing:
        raise ValueError(f"features ausentes no payload: {missing}")
    return frame[list(expected)]


def _as_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def predict(model: LoadedModel, payload: dict[str, Any]) -> tuple[str, float, int]:
    start = time.perf_counter()
    frame = to_features_frame(payload, model.feature_names)

    if hasattr(model.pipeline, "predict_proba"):
        proba = model.pipeline.predict_proba(frame)[0]
        idx = int(np.argmax(proba))
        perfil = str(model.classes[idx])
        score = float(proba[idx])
    else:
        perfil = str(model.pipeline.predict(frame)[0])
        score = 0.5

    latency_ms = max(int((time.perf_counter() - start) * 1000), 0)
    return perfil, _round(score), latency_ms


def _round(value: float) -> float:
    return float(np.round(value, 3))
