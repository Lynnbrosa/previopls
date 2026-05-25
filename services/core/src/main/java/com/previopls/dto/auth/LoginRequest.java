package com.previopls.dto.auth;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LoginRequest(
        @NotBlank(message = "email obrigatório")
        @Email(message = "email inválido")
        @Size(max = 180)
        String email,

        @NotBlank(message = "senha obrigatória")
        @Size(min = 6, max = 128)
        String senha
) {
}
