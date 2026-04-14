package com.vivero.module.auth.service.impl;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.dto.SocialLoginRequestDto;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.auth.service.AuthService;
import com.vivero.module.auth.service.oauth.SocialIdentityProfile;
import com.vivero.module.auth.service.oauth.SocialTokenVerifier;
import com.vivero.module.auth.util.JwtUtil;
import com.vivero.shared.enums.AuthProvider;
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

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtil;
    private final SocialTokenVerifier socialTokenVerifier;

    @Override
    @Transactional
    public AuthResponseDto login(LoginRequestDto request) {
        User existingUser = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + request.getEmail()));

        if (existingUser.getPassword() == null || existingUser.getPassword().isBlank()) {
            throw new BusinessException(
                    "This account must login with its social provider",
                    "LOCAL_LOGIN_NOT_AVAILABLE"
            );
        }

        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword())
        );

        existingUser.setLastLoginAt(LocalDateTime.now());
        User user = userRepository.save(existingUser);

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

        User user = User.builder()
                .firstName(request.getFirstName())
                .lastName(request.getLastName())
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(request.getRole())
                .active(true)
                .authProvider(AuthProvider.LOCAL)
                .emailVerified(true)
                .lastLoginAt(LocalDateTime.now())
                .build();

        userRepository.save(user);
        log.info("Nuevo usuario registrado: {} con rol {}", user.getEmail(), user.getRole());
        return buildAuthResponse(user);
    }

    @Override
    public AuthResponseDto refresh(RefreshTokenRequestDto request) {
        String refreshToken = request.getRefreshToken();

        final String email;
        try {
            email = jwtUtil.extractEmail(refreshToken);
        } catch (Exception ex) {
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

        return AuthResponseDto.builder()
                .accessToken(jwtUtil.generateAccessToken(user))
                .refreshToken(refreshToken)
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .role(user.getRole())
                .authProvider(user.getAuthProvider())
                .build();
    }

    @Override
    @Transactional
    public AuthResponseDto socialLogin(SocialLoginRequestDto request) {
        SocialIdentityProfile profile = socialTokenVerifier.verify(request.getProvider(), request.getIdToken());

        User user = userRepository.findByEmail(profile.getEmail())
                .map(existing -> mergeSocialProfile(existing, profile))
                .orElseGet(() -> createSocialUser(profile));

        user.setLastLoginAt(LocalDateTime.now());
        userRepository.save(user);

        log.info("Inicio de sesion social exitoso: {} con proveedor {}", user.getEmail(), user.getAuthProvider());
        return buildAuthResponse(user);
    }

    private AuthResponseDto buildAuthResponse(User user) {
        return AuthResponseDto.builder()
                .accessToken(jwtUtil.generateAccessToken(user))
                .refreshToken(jwtUtil.generateRefreshToken(user))
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .role(user.getRole())
                .authProvider(user.getAuthProvider())
                .build();
    }

    private User mergeSocialProfile(User existingUser, SocialIdentityProfile profile) {
        if (existingUser.getAuthProvider() != AuthProvider.LOCAL
                && existingUser.getAuthProvider() != profile.getProvider()) {
            throw new BusinessException(
                    "This email is already linked to a different social provider",
                    "SOCIAL_PROVIDER_MISMATCH"
            );
        }

        if (existingUser.getProviderUserId() != null
                && existingUser.getAuthProvider() == profile.getProvider()
                && !existingUser.getProviderUserId().equals(profile.getProviderUserId())) {
            throw new BusinessException(
                    "The social account does not match the existing user",
                    "SOCIAL_ACCOUNT_MISMATCH"
            );
        }

        existingUser.setAuthProvider(profile.getProvider());
        existingUser.setProviderUserId(profile.getProviderUserId());
        existingUser.setEmailVerified(profile.isEmailVerified());
        if (!profile.getFirstName().isBlank()) {
            existingUser.setFirstName(profile.getFirstName());
        }
        if (!profile.getLastName().isBlank()) {
            existingUser.setLastName(profile.getLastName());
        }
        existingUser.setAvatarUrl(profile.getAvatarUrl());
        return existingUser;
    }

    private User createSocialUser(SocialIdentityProfile profile) {
        return User.builder()
                .firstName(profile.getFirstName().isBlank() ? "Social" : profile.getFirstName())
                .lastName(profile.getLastName().isBlank() ? profile.getProvider().name() : profile.getLastName())
                .email(profile.getEmail())
                .password(null)
                .role(UserRole.VIEWER)
                .active(true)
                .authProvider(profile.getProvider())
                .providerUserId(profile.getProviderUserId())
                .emailVerified(profile.isEmailVerified())
                .avatarUrl(profile.getAvatarUrl())
                .lastLoginAt(LocalDateTime.now())
                .build();
    }
}
