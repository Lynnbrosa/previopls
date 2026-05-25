package com.previopls.dto.lead;

import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.StatusLead;

import java.time.Instant;
import java.util.UUID;

public record LeadListItemResponse(
        UUID id,
        UUID clienteId,
        UUID veiculoId,
        String nomeCliente,
        String modeloVeiculo,
        Double scoreRisco,
        PrioridadeLead prioridade,
        StatusLead status,
        Instant criadoEm
) {
}
