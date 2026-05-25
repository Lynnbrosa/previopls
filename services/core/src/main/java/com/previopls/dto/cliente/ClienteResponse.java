package com.previopls.dto.cliente;

import com.previopls.entity.enums.PerfilCliente;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record ClienteResponse(
        UUID id,
        String nome,
        String cpf,
        String email,
        String telefone,
        String regiao,
        PerfilCliente perfil,
        Double scoreRisco,
        Instant criadoEm,
        Instant classificadoEm,
        List<VeiculoResponse> veiculos
) {
}
