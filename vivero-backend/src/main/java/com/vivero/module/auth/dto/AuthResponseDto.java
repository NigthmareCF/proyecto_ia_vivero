package com.vivero.module.auth.dto;

import com.vivero.shared.enums.UserRole;
import lombok.Builder;
import lombok.Data;

/**
 * Respuesta devuelta al cliente tras un login o refresh exitoso.
 * El frontend almacena accessToken y refreshToken en memoria (no localStorage).
 */
@Data
@Builder
public class AuthResponseDto {

    // Token de acceso — se envía en cada request como: Authorization: Bearer <token>
    private String accessToken;

    // Token de refresco — solo se usa para obtener un nuevo accessToken
    private String refreshToken;

    // Tipo de token — siempre "Bearer" para que el frontend lo sepa
    @Builder.Default
    private String tokenType = "Bearer";

    // Datos básicos del usuario para mostrar en la UI sin hacer otro request
    private Long userId;
    private String fullName;
    private String email;
    private UserRole role;
}
