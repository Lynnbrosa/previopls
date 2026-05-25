from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Perfil = Literal["FIEL", "ABANDONO", "ESQUECIDO", "ECONOMICO"]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regiao: str = Field(min_length=1, max_length=64)
    modelo: str = Field(min_length=1, max_length=64)
    ano: int = Field(ge=1990, le=2100)
    valor_compra: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    concessionaria_id: str = Field(min_length=1, max_length=64)


class PredictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    perfil: Perfil
    score: float = Field(ge=0.0, le=1.0)
    latency_ms: int = Field(ge=0)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_version: str


class VersionResponse(BaseModel):
    name: str
    version: str
    model_version: str
