from pathlib import Path

import joblib
import pytest
from sklearn.dummy import DummyClassifier

from app.predictor import _check_anti_leakage, _validate_classes, load_model, predict


def test_load_model_exposes_d0_features_and_contract_classes(model_path: Path):
    model = load_model(model_path)
    assert set(model.feature_names) == {"regiao", "modelo", "ano", "valor_compra", "concessionaria_id"}
    assert set(model.classes) <= {"FIEL", "ABANDONO", "ESQUECIDO", "ECONOMICO"}
    assert model.version.startswith("sha256:")


def test_predict_returns_contract_tuple(model_path: Path):
    model = load_model(model_path)
    perfil, score, latency_ms = predict(
        model,
        {"regiao": "SP", "modelo": "Ranger", "ano": 2026, "valor_compra": "250000.00", "concessionaria_id": "FORD-SP-001"},
    )
    assert perfil in {"FIEL", "ABANDONO", "ESQUECIDO", "ECONOMICO"}
    assert 0.0 <= score <= 1.0
    assert latency_ms >= 0


@pytest.mark.parametrize(
    "features",
    [
        ("regiao", "recency_days"),
        ("modelo", "Frequency"),
        ("ano", "monetary_total"),
        ("valor_compra", "tenure_months"),
        ("regiao", "r_score"),
        ("regiao", "f_score"),
        ("regiao", "m_score"),
    ],
)
def test_anti_leakage_rejects_post_sale_features(features):
    with pytest.raises(RuntimeError, match="US02"):
        _check_anti_leakage(features)


def test_anti_leakage_accepts_pure_d0_features():
    _check_anti_leakage(("regiao", "modelo", "ano", "valor_compra", "concessionaria_id"))


def test_validate_classes_rejects_unknown_profile():
    with pytest.raises(RuntimeError, match="fora do contrato"):
        _validate_classes(("FIEL", "VIP"))


def test_load_model_fails_when_pipeline_has_no_feature_names(tmp_path: Path):
    clf = DummyClassifier(strategy="most_frequent").fit([[0], [1]], ["FIEL", "ABANDONO"])
    path = tmp_path / "bad.pkl"
    joblib.dump(clf, path)
    with pytest.raises(RuntimeError, match="feature_names_in_"):
        load_model(path)


def test_load_model_fails_when_file_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_model(tmp_path / "nope.pkl")
