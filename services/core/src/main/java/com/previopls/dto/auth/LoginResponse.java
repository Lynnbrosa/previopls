package com.previopls.dto.auth;

public record LoginResponse(
        String accessToken,
        String tokenType,
        long expiresIn,
        String role
) {
}
