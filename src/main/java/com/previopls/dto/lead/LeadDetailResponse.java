package com.previopls.dto.lead;

import com.previopls.dto.cliente.ClienteResponse;
import com.previopls.dto.cliente.VeiculoResponse;
import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.StatusLead;

import java.time.Instant;
import java.util.UUID;

public record LeadDetailResponse(
        UUID id,
        Double scoreRisco,
        PrioridadeLead prioridade,
        StatusLead status,
        String scriptOferta,
        String observacao,
        Instant criadoEm,
        Instant atualizadoEm,
        ClienteResponse cliente,
        VeiculoResponse veiculo
) {
}
