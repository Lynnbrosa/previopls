package com.previopls.dto.cliente;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;

public record ClienteCreateRequest(
        @NotBlank @Size(min = 2, max = 180) String nome,
        @NotBlank
        @Pattern(regexp = "^\\d{11}$", message = "CPF deve conter 11 dígitos numéricos")
        String cpf,
        @Email @Size(max = 180) String email,
        @Size(max = 20) String telefone,
        @NotBlank @Size(min = 2, max = 40) String regiao,
        @NotNull @Valid VeiculoRequest veiculo
) {
}
