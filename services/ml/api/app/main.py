from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.logging import configure_logging, get_logger
from app.predictor import LoadedModel, load_model, predict
from app.schemas import HealthResponse, PredictRequest, PredictResponse, VersionResponse

log = get_logger("ml-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    model = load_model()
    app.state.model = model
    yield
    app.state.model = None


app = FastAPI(
    title="PrevioPLS · ml-api",
    version="1.0.0",
    description="Servidor de inferência D0 para o motor preditivo de retenção pós-venda.",
    lifespan=lifespan,
)


def _model(request: Request) -> LoadedModel:
    model: LoadedModel | None = request.app.state.model
    if model is None:
        raise HTTPException(status_code=503, detail="modelo não carregado")
    return model


@app.post("/predict", response_model=PredictResponse)
def post_predict(payload: PredictRequest, request: Request) -> PredictResponse:
    model = _model(request)
    perfil, score, latency_ms = predict(model, payload.model_dump(mode="json"))
    log.info(
        "prediction",
        perfil=perfil,
        score=score,
        latency_ms=latency_ms,
        regiao=payload.regiao,
        modelo=payload.modelo,
        ano=payload.ano,
    )
    return PredictResponse(perfil=perfil, score=score, latency_ms=latency_ms)


@app.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    model: LoadedModel | None = request.app.state.model
    if model is None:
        return HealthResponse(status="degraded", model_loaded=False, model_version="unknown")
    return HealthResponse(status="ok", model_loaded=True, model_version=model.version)


@app.get("/version", response_model=VersionResponse)
def get_version(request: Request) -> VersionResponse:
    model: LoadedModel | None = request.app.state.model
    model_version = model.version if model else "unknown"
    return VersionResponse(name="previopls-ml-api", version="1.0.0", model_version=model_version)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Erro inesperado no ml-api"}},
    )
