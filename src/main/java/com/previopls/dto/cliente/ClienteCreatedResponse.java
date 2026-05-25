package com.previopls.dto.cliente;

import com.previopls.entity.enums.PerfilCliente;

import java.util.UUID;

public record ClienteCreatedResponse(
        ClienteResponse cliente,
        UUID leadId,
        PerfilCliente perfil,
        Double scoreRisco
) {
}
