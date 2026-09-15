PAYLOAD = {
    "regiao": "SP",
    "modelo": "Ranger",
    "ano": 2026,
    "valor_compra": "250000.00",
    "concessionaria_id": "FORD-SP-001",
}


def test_health_reports_loaded_model(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"].startswith("sha256:")


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json()["name"] == "previopls-ml-api"


def test_predict_contract(client):
    r = client.post("/predict", json=PAYLOAD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["perfil"] in {"FIEL", "ABANDONO", "ESQUECIDO", "ECONOMICO"}
    assert 0.0 <= body["score"] <= 1.0
    assert body["latency_ms"] >= 0


def test_predict_is_deterministic(client):
    a = client.post("/predict", json=PAYLOAD).json()
    b = client.post("/predict", json=PAYLOAD).json()
    assert (a["perfil"], a["score"]) == (b["perfil"], b["score"])


def test_predict_handles_unknown_categories(client):
    r = client.post("/predict", json={**PAYLOAD, "regiao": "ZZ", "modelo": "Modelo Novo", "concessionaria_id": "FORD-ZZ-999"})
    assert r.status_code == 200, r.text


def test_predict_rejects_post_sale_fields_us02(client):
    r = client.post("/predict", json={**PAYLOAD, "recency": 10})
    assert r.status_code == 422


def test_predict_rejects_missing_fields(client):
    r = client.post("/predict", json={"regiao": "SP"})
    assert r.status_code == 422
