package com.vivero.module.auth.service.impl;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.auth.service.AuthService;
import com.vivero.module.auth.util.JwtUtil;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Implementación del servicio de autenticación.
 *
 * Flujo de login:
 * 1. AuthenticationManager verifica email + password contra la DB
 * 2. Si es correcto, JwtUtil genera access token y refresh token
 * 3. Se devuelve AuthResponseDto con ambos tokens y datos del usuario
 *
 * Flujo de refresh:
 * 1. Se valida que el refresh token no esté expirado
 * 2. Se extrae el email del token
 * 3. Se carga el usuario de la DB
 * 4. Se genera un nuevo access token
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;

    @Override
    public AuthResponseDto login(LoginRequestDto request) {
        // AuthenticationManager lanza BadCredentialsException si las credenciales son incorrectas
        // GlobalExceptionHandler la convierte en HTTP 401
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getEmail(),
                        request.getPassword()
                )
        );

        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new ResourceNotFoundException(
                        "User not found: " + request.getEmail()));

        log.info("Inicio de sesión exitoso: {}", user.getEmail());

        return buildAuthResponse(user);
    }

    @Override
    @Transactional
    public AuthResponseDto register(RegisterRequestDto request) {
        // Verificar que el email no esté ya registrado
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new BusinessException(
                    "Email already registered: " + request.getEmail(),
                    "EMAIL_ALREADY_EXISTS"
            );
        }

        User user = User.builder()
                .firstName(request.getFirstName())
                .lastName(request.getLastName())
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(request.getRole())
                .active(true)
                .build();

        userRepository.save(user);
        log.info("Nuevo usuario registrado: {} con rol {}", user.getEmail(), user.getRole());

        return buildAuthResponse(user);
    }

    @Override
    public AuthResponseDto refresh(RefreshTokenRequestDto request) {
        final String refreshToken = request.getRefreshToken();

        // Extraer email del refresh token
        final String email;
        try {
            email = jwtUtil.extractEmail(refreshToken);
        } catch (Exception e) {
            throw new BusinessException("Invalid refresh token", "INVALID_REFRESH_TOKEN");
        }

        // Verificar que el token no esté expirado
        if (jwtUtil.isTokenExpired(refreshToken)) {
            throw new BusinessException(
                    "Refresh token expired, please login again",
                    "REFRESH_TOKEN_EXPIRED"
            );
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

        // Generar nuevo access token — el refresh token se reutiliza hasta que expire
        String newAccessToken = jwtUtil.generateAccessToken(user);

        return AuthResponseDto.builder()
                .accessToken(newAccessToken)
                .refreshToken(refreshToken)
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .role(user.getRole())
                .build();
    }

    // ── Método auxiliar ───────────────────────────────────────────────────────

    private AuthResponseDto buildAuthResponse(User user) {
        return AuthResponseDto.builder()
                .accessToken(jwtUtil.generateAccessToken(user))
                .refreshToken(jwtUtil.generateRefreshToken(user))
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .role(user.getRole())
                .build();
    }
}
