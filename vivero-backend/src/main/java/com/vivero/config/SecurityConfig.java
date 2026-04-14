package com.vivero.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

/**
 * Configuración central de Spring Security.
 *
 * Decisiones de diseño:
 * - STATELESS: no hay sesiones en servidor, todo se valida por JWT
 * - CSRF deshabilitado: innecesario con JWT stateless
 * - CORS habilitado: frontend en :3000 habla con backend en :8080
 * - BCrypt para passwords: factor de costo 12 (balance seguridad/velocidad)
 * - @EnableMethodSecurity: permite @PreAuthorize en los controllers
 *
 * Rutas públicas (sin token):
 *   POST /auth/login
 *   POST /auth/refresh
 *   GET  /actuator/health
 *   WS   /ws/**
 *
 * Todo lo demás requiere token JWT válido.
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;
    private final UserDetailsService userDetailsService;
    private final AppProperties appProperties;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // Deshabilitar CSRF — no aplica con JWT stateless
            .csrf(AbstractHttpConfigurer::disable)

            // CORS — permite que el frontend en :3000 consuma la API
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))

            // Rutas públicas vs protegidas
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                    "/auth/login",
                    "/api/auth/login",
                    "/auth/social",
                    "/api/auth/social",
                    "/auth/refresh",
                    "/api/auth/refresh",
                    "/actuator/health",
                    "/api/actuator/health",
                    "/actuator/info",
                    "/api/actuator/info",
                    "/ws/**",
                    "/api/ws/**"      // WebSocket — autenticación propia vía token en handshake
                ).permitAll()
                .anyRequest().authenticated()
            )

            // Sin sesiones en servidor — 100% stateless
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // Proveedor de autenticación personalizado
            .authenticationProvider(authenticationProvider())

            // Insertar el filtro JWT antes del filtro estándar de usuario/contraseña
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public AuthenticationProvider authenticationProvider() {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        // Carga el usuario desde la DB por email
        provider.setUserDetailsService(userDetailsService);
        // Verifica la contraseña con BCrypt
        provider.setPasswordEncoder(passwordEncoder());
        return provider;
    }

    @Bean
    public AuthenticationManager authenticationManager(
            AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        // Factor 12 — recomendado para producción (ajustar a 10 si CPU es limitada)
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();

        // Orígenes permitidos — configurable por variable de entorno para dev/demo
        config.setAllowedOriginPatterns(appProperties.getCors().getAllowedOriginPatterns());

        // Métodos HTTP permitidos
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));

        // Headers permitidos en los requests
        config.setAllowedHeaders(List.of("Authorization", "Content-Type", "Accept"));

        // Exponer el header Authorization en las respuestas
        config.setExposedHeaders(List.of("Authorization"));

        config.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
