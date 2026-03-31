package com.vivero.module.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Datos que el cliente envía para renovar el access token expirado.
 * El refreshToken tiene una vida de 7 días — mucho más que el accessToken (24h).
 */
@Data
public class RefreshTokenRequestDto {

    @NotBlank(message = "Refresh token is required")
    private String refreshToken;
}
