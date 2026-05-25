package com.previopls.dto.cliente;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

public record VeiculoResponse(
        UUID id,
        String modelo,
        String versao,
        Integer ano,
        String vin,
        LocalDate dataCompra,
        BigDecimal valorCompra,
        String concessionariaId
) {
}
