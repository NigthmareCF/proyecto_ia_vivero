package com.vivero.module.auth.service.impl;

import com.google.api.client.googleapis.auth.oauth2.GoogleIdToken;
import com.google.api.client.googleapis.auth.oauth2.GoogleIdTokenVerifier;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.gson.GsonFactory;
import com.vivero.config.AppProperties;
import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.GoogleLoginRequestDto;
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

import java.security.SecureRandom;
import java.util.Base64;
import java.util.Collections;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    private final AppProperties appProperties;
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
    public AuthResponseDto loginWithGoogle(GoogleLoginRequestDto request) {
        String googleClientId = appProperties.getAuth().getGoogle().getClientId();
        if (googleClientId == null || googleClientId.isBlank()) {
            throw new BusinessException("Google OAuth is not configured", "GOOGLE_OAUTH_NOT_CONFIGURED");
        }

        GoogleIdToken.Payload payload = verifyGoogleToken(request.getIdToken(), googleClientId);
        String email = payload.getEmail();
        if (email == null || email.isBlank()) {
            throw new BusinessException("Google account email is missing", "GOOGLE_EMAIL_REQUIRED");
        }

        Object emailVerified = payload.get("email_verified");
        if (!(emailVerified instanceof Boolean verified) || !verified) {
            throw new BusinessException("Google account email is not verified", "GOOGLE_EMAIL_NOT_VERIFIED");
        }

        User user = userRepository.findByEmail(email)
                .orElseGet(() -> createGoogleUser(payload));

        if (!user.isEnabled()) {
            throw new BusinessException("User is inactive", "USER_INACTIVE");
        }

        log.info("Inicio de sesion con Google exitoso: {}", user.getEmail());
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
                .phoneNumber(normalizePhone(request.getPhoneNumber()))
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

        user.setPhoneNumber(normalizePhone(request.getPhoneNumber()));
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

    private GoogleIdToken.Payload verifyGoogleToken(String idTokenString, String clientId) {
        try {
            GoogleIdTokenVerifier verifier = new GoogleIdTokenVerifier.Builder(
                    new NetHttpTransport(),
                    GsonFactory.getDefaultInstance()
            )
                    .setAudience(Collections.singletonList(clientId))
                    .build();

            GoogleIdToken idToken = verifier.verify(idTokenString);
            if (idToken == null) {
                throw new BusinessException("Invalid Google ID token", "INVALID_GOOGLE_TOKEN");
            }

            return idToken.getPayload();
        } catch (BusinessException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new BusinessException("Google ID token validation failed", "GOOGLE_TOKEN_VALIDATION_FAILED");
        }
    }

    private User createGoogleUser(GoogleIdToken.Payload payload) {
        String email = payload.getEmail();
        String firstName = firstNonBlank((String) payload.get("given_name"), "Google");
        String lastName = firstNonBlank((String) payload.get("family_name"), "User");

        User user = User.builder()
                .firstName(firstName)
                .lastName(lastName)
                .email(email)
                .password(passwordEncoder.encode(generateRandomPassword()))
                .role(UserRole.VIEWER)
                .active(true)
                .build();

        userRepository.save(user);
        log.info("Nuevo usuario registrado por Google OAuth: {} con rol {}", user.getEmail(), user.getRole());
        return user;
    }

    private String normalizePhone(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }

    private String firstNonBlank(String value, String fallback) {
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return value.trim();
    }

    private String generateRandomPassword() {
        byte[] randomBytes = new byte[24];
        SECURE_RANDOM.nextBytes(randomBytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(randomBytes);
    }
}
