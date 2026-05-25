package com.previopls.dto.cliente;

import jakarta.validation.constraints.*;

import java.math.BigDecimal;
import java.time.LocalDate;

public record VeiculoRequest(
        @NotBlank @Size(max = 80) String modelo,
        @NotBlank @Size(max = 80) String versao,
        @NotNull @Min(2000) @Max(2100) Integer ano,
        @NotBlank
        @Size(min = 17, max = 17, message = "VIN deve ter 17 caracteres")
        @Pattern(regexp = "^[A-HJ-NPR-Z0-9]{17}$", message = "VIN inválido (alfanumérico sem I/O/Q)")
        String vin,
        @NotNull LocalDate dataCompra,
        @NotNull @DecimalMin(value = "0.0", inclusive = true) BigDecimal valorCompra,
        @NotBlank @Size(max = 40) String concessionariaId
) {
}
