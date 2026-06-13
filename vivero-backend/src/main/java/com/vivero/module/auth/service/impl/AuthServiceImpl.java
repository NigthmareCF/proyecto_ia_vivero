package com.vivero.module.auth.service.impl;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.dto.UpdateProfileRequestDto;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.auth.service.AuthService;
import com.vivero.module.auth.util.JwtUtil;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getEmail(),
                        request.getPassword()
                )
        );

        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + request.getEmail()));

        log.info("Inicio de sesion exitoso: {}", user.getEmail());
        return buildAuthResponse(user);
    }

    @Override
    @Transactional
    public AuthResponseDto register(RegisterRequestDto request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new BusinessException(
                    "Email already registered: " + request.getEmail(),
                    "EMAIL_ALREADY_EXISTS"
            );
        }

        UserRole requestedRole = normalizePublicRole(request.getRole());

        User user = User.builder()
                .firstName(request.getFirstName())
                .lastName(request.getLastName())
                .email(request.getEmail())
                .phoneNumber(normalizePhone(request.getPhoneNumber()))
                .password(passwordEncoder.encode(request.getPassword()))
                .role(requestedRole)
                .active(true)
                .build();

        userRepository.save(user);
        log.info("Nuevo usuario registrado: {} con rol {}", user.getEmail(), user.getRole());
        return buildAuthResponse(user);
    }

    @Override
    public AuthResponseDto refresh(RefreshTokenRequestDto request) {
        final String refreshToken = request.getRefreshToken();

        final String email;
        try {
            email = jwtUtil.extractEmail(refreshToken);
        } catch (Exception e) {
            throw new BusinessException("Invalid refresh token", "INVALID_REFRESH_TOKEN");
        }

        if (jwtUtil.isTokenExpired(refreshToken)) {
            throw new BusinessException(
                    "Refresh token expired, please login again",
                    "REFRESH_TOKEN_EXPIRED"
            );
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

        String newAccessToken = jwtUtil.generateAccessToken(user);

        return AuthResponseDto.builder()
                .accessToken(newAccessToken)
                .refreshToken(refreshToken)
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phoneNumber(user.getPhoneNumber())
                .role(user.getRole())
                .build();
    }

    @Override
    @Transactional
    public AuthResponseDto updateProfile(String currentUserEmail, UpdateProfileRequestDto request) {
        User user = userRepository.findByEmail(currentUserEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + currentUserEmail));

        if (!user.getEmail().equalsIgnoreCase(request.getEmail().trim())
                && userRepository.existsByEmail(request.getEmail().trim())) {
            throw new BusinessException("Email already registered: " + request.getEmail(), "EMAIL_ALREADY_EXISTS");
        }

        user.setFirstName(request.getFirstName().trim());
        user.setLastName(request.getLastName().trim());
        user.setEmail(request.getEmail().trim());
        user.setPhoneNumber(normalizePhone(request.getPhoneNumber()));
        if (request.getPassword() != null && !request.getPassword().isBlank()) {
            user.setPassword(passwordEncoder.encode(request.getPassword()));
        }
        userRepository.save(user);

        log.info("Perfil actualizado para {}", user.getEmail());
        return buildAuthResponse(user);
    }

    private AuthResponseDto buildAuthResponse(User user) {
        return AuthResponseDto.builder()
                .accessToken(jwtUtil.generateAccessToken(user))
                .refreshToken(jwtUtil.generateRefreshToken(user))
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phoneNumber(user.getPhoneNumber())
                .role(user.getRole())
                .build();
    }

    private String normalizePhone(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }

    private UserRole normalizePublicRole(UserRole role) {
        if (role == null) {
            throw new BusinessException("Role is required", "ROLE_REQUIRED");
        }
        if (role == UserRole.CONTROLLER || role == UserRole.VIEWER) {
            return role;
        }
        throw new BusinessException("Only CONTROLLER or VIEWER roles are allowed for self-registration", "INVALID_PUBLIC_ROLE");
    }
}
