package com.vivero.module.auth.controller;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.GoogleLoginRequestDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.dto.UpdateProfileRequestDto;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.service.AuthService;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/**
 * Controlador REST del módulo de autenticación.
 *
 * Endpoints públicos (sin token):
 *   POST /api/auth/login    — iniciar sesión
 *   POST /api/auth/refresh  — renovar access token
 *
 * Endpoints protegidos:
 *   POST /api/auth/register — registrar usuario (solo ADMIN)
 *   GET  /api/auth/me       — datos del usuario autenticado
 *
 * El controlador NO tiene lógica de negocio — solo recibe, valida y delega a AuthService.
 */
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * Inicia sesión con email y contraseña.
     * Devuelve access token (24h) y refresh token (7 días).
     *
     * POST /api/auth/login
     * Body: { "email": "admin@vivero.com", "password": "password123" }
     */
    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponseDto>> login(
            @Valid @RequestBody LoginRequestDto request) {

        AuthResponseDto response = authService.login(request);
        return ResponseEntity.ok(ApiResponse.ok("Login successful", response));
    }

    @PostMapping("/google")
    public ResponseEntity<ApiResponse<AuthResponseDto>> googleLogin(
            @Valid @RequestBody GoogleLoginRequestDto request) {

        AuthResponseDto response = authService.loginWithGoogle(request);
        return ResponseEntity.ok(ApiResponse.ok("Google login successful", response));
    }

    /**
     * Registra un nuevo usuario en el sistema.
     * Solo un usuario con rol ADMIN puede ejecutar este endpoint.
     *
     * POST /api/auth/register
     * Header: Authorization: Bearer <admin_token>
     * Body: { "firstName": "Ana", "lastName": "García", "email": "ana@vivero.com",
     *         "password": "password123", "role": "OPERATOR" }
     */
    @PostMapping("/register")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<AuthResponseDto>> register(
            @Valid @RequestBody RegisterRequestDto request) {

        AuthResponseDto response = authService.register(request);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.ok("User registered successfully", response));
    }

    /**
     * Renueva el access token usando el refresh token.
     * Si el refresh token expiró, el usuario debe hacer login nuevamente.
     *
     * POST /api/auth/refresh
     * Body: { "refreshToken": "<refresh_token>" }
     */
    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<AuthResponseDto>> refresh(
            @Valid @RequestBody RefreshTokenRequestDto request) {

        AuthResponseDto response = authService.refresh(request);
        return ResponseEntity.ok(ApiResponse.ok("Token refreshed successfully", response));
    }

    /**
     * Devuelve los datos del usuario autenticado actualmente.
     * El frontend usa esto para mostrar nombre y rol en la barra de navegación.
     *
     * GET /api/auth/me
     * Header: Authorization: Bearer <token>
     */
    @GetMapping("/me")
    public ResponseEntity<ApiResponse<AuthResponseDto>> me(
            org.springframework.security.core.Authentication authentication) {

        User user = (User) authentication.getPrincipal();

        AuthResponseDto response = AuthResponseDto.builder()
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phoneNumber(user.getPhoneNumber())
                .role(user.getRole())
                .build();

        return ResponseEntity.ok(ApiResponse.ok("User data retrieved", response));
    }

    @PutMapping("/me")
    public ResponseEntity<ApiResponse<AuthResponseDto>> updateProfile(
            @Valid @RequestBody UpdateProfileRequestDto request,
            org.springframework.security.core.Authentication authentication) {

        User user = (User) authentication.getPrincipal();
        AuthResponseDto response = authService.updateProfile(user.getEmail(), request);
        return ResponseEntity.ok(ApiResponse.ok("User profile updated", response));
    }
}
