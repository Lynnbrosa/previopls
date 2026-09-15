from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import Principal, Role, requires_role
from app.db.session import get_db
from app.models import AuditAction, PrioridadeLead, StatusLead
from app.schemas.lead import LeadDetail, LeadListResponse, LeadPatchRequest
from app.services.alert_service import maybe_alert_mass_query
from app.services.audit_service import AuditService
from app.services.core_client import CoreClient, passthrough
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])

_PROXY_NOTE = (
    " Com CORE_API_URL configurado a resposta vem do Core (contrato camelCase: "
    "nomeCliente, scoreRisco, perPage...). Sem CORE_API_URL vale o schema abaixo (snake_case)."
)


@router.get(
    "",
    response_model=LeadListResponse,
    summary="Lista leads priorizados (paginado)",
    description="Ordenação: prioridade (crítica > alta > média > baixa), score desc, criação desc." + _PROXY_NOTE,
)
def listar(
    request: Request,
    prioridade: Optional[PrioridadeLead] = Query(default=None),
    status: Optional[StatusLead] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    principal: Principal = Depends(requires_role(Role.CONSULTOR, Role.ADMIN, Role.ANALISTA)),
) -> Response | LeadListResponse:
    settings = get_settings()
    if settings.core_proxy_enabled:
        maybe_alert_mass_query(principal.user_id, AuditService(db), request)
        db.commit()
        upstream = CoreClient().forward(
            "GET",
            "/v1/leads",
            principal=principal,
            request=request,
            params={
                "prioridade": prioridade.value if prioridade else None,
                "status": status.value if status else None,
                "page": page,
                "per_page": per_page,
            },
        )
        return passthrough(upstream)

    service = LeadService(db)
    result = service.listar(
        prioridade=prioridade,
        status=status,
        page=page,
        per_page=per_page,
        request=request,
        principal_id=principal.user_id,
    )
    db.commit()
    return result


@router.get(
    "/{lead_id}",
    response_model=LeadDetail,
    summary="Visão 360 do lead (cliente + veículo + script comercial)",
    description="PII sempre mascarada." + _PROXY_NOTE,
)
def obter(
    lead_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(requires_role(Role.CONSULTOR, Role.ADMIN, Role.ANALISTA)),
) -> Response | LeadDetail:
    if get_settings().core_proxy_enabled:
        upstream = CoreClient().forward("GET", f"/v1/leads/{lead_id}", principal=principal, request=request)
        return passthrough(upstream)
    return LeadService(db).obter(lead_id)


@router.patch(
    "/{lead_id}",
    response_model=LeadDetail,
    summary="Registra o resultado da abordagem (agendado / recusado / sem-contato)",
    description="Revisão humana da recomendação automática (LGPD Art. 20)." + _PROXY_NOTE,
)
def atualizar(
    lead_id: UUID,
    payload: LeadPatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    principal: Principal = Depends(requires_role(Role.CONSULTOR, Role.ADMIN)),
) -> Response | LeadDetail:
    if get_settings().core_proxy_enabled:
        upstream = CoreClient().forward(
            "PATCH",
            f"/v1/leads/{lead_id}",
            principal=principal,
            request=request,
            json={"status": payload.status.value, "observacao": payload.observacao},
        )
        if upstream.status_code == status.HTTP_200_OK:
            AuditService(db).log_event(
                action=AuditAction.LEAD_PATCHED,
                request=request,
                entity_type="Lead",
                entity_id=str(lead_id),
                details=f"status -> {payload.status.value} via=core",
            )
            db.commit()
        return passthrough(upstream)

    service = LeadService(db)
    result = service.atualizar_status(lead_id, payload, request)
    db.commit()
    return result
