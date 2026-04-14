package com.vivero.module.auth;

import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.SocialLoginRequestDto;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.auth.service.impl.AuthServiceImpl;
import com.vivero.module.auth.service.oauth.SocialIdentityProfile;
import com.vivero.module.auth.service.oauth.SocialTokenVerifier;
import com.vivero.module.auth.util.JwtUtil;
import com.vivero.shared.enums.AuthProvider;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private AuthenticationManager authenticationManager;

    @Mock
    private JwtUtil jwtUtil;

    @Mock
    private SocialTokenVerifier socialTokenVerifier;

    private AuthServiceImpl authService;

    @BeforeEach
    void setUp() {
        authService = new AuthServiceImpl(
                userRepository,
                passwordEncoder,
                authenticationManager,
                jwtUtil,
                socialTokenVerifier
        );
    }

    @Test
    void loginShouldRejectLocalAuthForSocialOnlyAccount() {
        User socialUser = User.builder()
                .firstName("Ana")
                .lastName("Google")
                .email("ana@vivero.com")
                .password(null)
                .role(UserRole.VIEWER)
                .authProvider(AuthProvider.GOOGLE)
                .build();

        when(userRepository.findByEmail("ana@vivero.com")).thenReturn(Optional.of(socialUser));

        LoginRequestDto request = new LoginRequestDto();
        request.setEmail("ana@vivero.com");
        request.setPassword("secret");

        assertThrows(BusinessException.class, () -> authService.login(request));
    }

    @Test
    void socialLoginShouldAutoCreateViewerUser() {
        SocialLoginRequestDto request = new SocialLoginRequestDto();
        request.setProvider(AuthProvider.GOOGLE);
        request.setIdToken("token");

        SocialIdentityProfile profile = SocialIdentityProfile.builder()
                .provider(AuthProvider.GOOGLE)
                .providerUserId("google-sub-1")
                .email("ana@vivero.com")
                .emailVerified(true)
                .firstName("Ana")
                .lastName("Gomez")
                .fullName("Ana Gomez")
                .avatarUrl("https://img.test/avatar.png")
                .build();

        when(socialTokenVerifier.verify(AuthProvider.GOOGLE, "token")).thenReturn(profile);
        when(userRepository.findByEmail("ana@vivero.com")).thenReturn(Optional.empty());
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(10L);
            return user;
        });
        when(jwtUtil.generateAccessToken(any(User.class))).thenReturn("access");
        when(jwtUtil.generateRefreshToken(any(User.class))).thenReturn("refresh");

        var response = authService.socialLogin(request);

        assertEquals("ana@vivero.com", response.getEmail());
        assertEquals(UserRole.VIEWER, response.getRole());
        assertEquals(AuthProvider.GOOGLE, response.getAuthProvider());
    }

    @Test
    void socialLoginShouldRejectDifferentLinkedProvider() {
        SocialLoginRequestDto request = new SocialLoginRequestDto();
        request.setProvider(AuthProvider.APPLE);
        request.setIdToken("token");

        SocialIdentityProfile profile = SocialIdentityProfile.builder()
                .provider(AuthProvider.APPLE)
                .providerUserId("apple-sub-1")
                .email("ana@vivero.com")
                .emailVerified(true)
                .firstName("Ana")
                .lastName("Apple")
                .fullName("Ana Apple")
                .build();

        User existingUser = User.builder()
                .firstName("Ana")
                .lastName("Google")
                .email("ana@vivero.com")
                .password(null)
                .role(UserRole.VIEWER)
                .authProvider(AuthProvider.GOOGLE)
                .providerUserId("google-sub-1")
                .build();

        when(socialTokenVerifier.verify(AuthProvider.APPLE, "token")).thenReturn(profile);
        when(userRepository.findByEmail("ana@vivero.com")).thenReturn(Optional.of(existingUser));

        assertThrows(BusinessException.class, () -> authService.socialLogin(request));
    }
}
