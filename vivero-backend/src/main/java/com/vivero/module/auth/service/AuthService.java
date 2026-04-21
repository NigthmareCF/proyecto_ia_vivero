package com.vivero.module.auth.service;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.GoogleLoginRequestDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.dto.UpdateProfileRequestDto;

/**
 * Contrato del servicio de autenticación.
 * La implementación concreta está en AuthServiceImpl.
 *
 * Separar interfaz de implementación permite:
 * - Testear con mocks sin levantar el contexto de Spring
 * - Cambiar la implementación sin tocar los controladores
 */
public interface AuthService {

    /**
     * Autentica al usuario con email y contraseña.
     * Devuelve access token + refresh token si las credenciales son correctas.
     */
    AuthResponseDto login(LoginRequestDto request);

    AuthResponseDto loginWithGoogle(GoogleLoginRequestDto request);

    /**
     * Registra un nuevo usuario en el sistema.
     * Solo puede ser llamado por un usuario con rol ADMIN.
     * Devuelve los tokens para que el admin pueda ver la cuenta creada.
     */
    AuthResponseDto register(RegisterRequestDto request);

    /**
     * Genera un nuevo access token usando el refresh token.
     * Si el refresh token expiró, el usuario debe volver a hacer login.
     */
    AuthResponseDto refresh(RefreshTokenRequestDto request);

    AuthResponseDto updateProfile(String currentUserEmail, UpdateProfileRequestDto request);
}
