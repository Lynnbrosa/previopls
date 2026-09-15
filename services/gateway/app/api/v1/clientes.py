from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.hmac_signing import require_hmac_signature
from app.core.security import Principal, Role, requires_role
from app.db.session import get_db
from app.models import AuditAction
from app.schemas.cliente import ClienteCreate, ClienteCreatedResponse
from app.services.audit_service import AuditService
from app.services.cliente_service import ClienteService
from app.services.core_client import CoreClient, passthrough, to_core_payload

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post(
    "",
    response_model=ClienteCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_hmac_signature)],  # HMAC obrigatório em payload crítico (LGPD)
    summary="Cadastro D0 da compra (webhook do faturamento)",
    description=(
        "Valida HMAC + JWT admin + schema e dispara a classificação preditiva. "
        "Com CORE_API_URL configurado, o payload é repassado ao Core (JWT interno HS256) "
        "e a resposta do Core é devolvida tal qual (contrato camelCase). "
        "Sem CORE_API_URL, o Gateway persiste o domínio localmente (modo standalone)."
    ),
)
def criar_cliente(
    payload: ClienteCreate,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(requires_role(Role.ADMIN)),
) -> Response | ClienteCreatedResponse:
    settings = get_settings()
    if settings.core_proxy_enabled:
        upstream = CoreClient().forward(
            "POST", "/v1/clientes", principal=principal, request=request, json=to_core_payload(payload)
        )
        if upstream.status_code == status.HTTP_201_CREATED:
            _audit_created(db, request, upstream.json())
            db.commit()
        return passthrough(upstream)

    service = ClienteService(db)
    result = service.cadastrar_compra(payload, request)
    db.commit()
    return result


def _audit_created(db: Session, request: Request, body: dict) -> None:
    """Audit de borda correlacionado ao Core pelo X-Request-Id (sem PII)."""
    audit = AuditService(db)
    cliente_id: Optional[str] = (body.get("cliente") or {}).get("id")
    perfil = body.get("perfil")
    score = body.get("scoreRisco")
    audit.log_event(
        action=AuditAction.CLIENTE_CREATED,
        request=request,
        entity_type="Cliente",
        entity_id=str(cliente_id) if cliente_id else None,
        details=f"perfil={perfil} score={score} via=core",
    )
    lead_id: Optional[UUID | str] = body.get("leadId")
    if lead_id:
        audit.log_event(
            action=AuditAction.LEAD_CREATED,
            request=request,
            entity_type="Lead",
            entity_id=str(lead_id),
            details="via=core",
        )
