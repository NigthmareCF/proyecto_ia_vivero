package com.vivero.module.auth.util;

import com.vivero.config.AppProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

/**
 * Utilidad central para todo lo relacionado con JWT.
 *
 * Flujo de uso:
 * 1. Usuario hace login → AuthService llama generateAccessToken()
 * 2. Frontend guarda el token y lo envía en cada request como:
 *    Header: Authorization: Bearer <token>
 * 3. JwtAuthFilter intercepta el request y llama isTokenValid()
 * 4. Si el token expira, el frontend llama /auth/refresh con el refreshToken
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtUtil {

    private final AppProperties appProperties;

    // ── Generación de tokens ──────────────────────────────────────────────────

    /**
     * Genera un access token para el usuario autenticado.
     * Incluye el email como subject y el rol como claim adicional.
     */
    public String generateAccessToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("role", userDetails.getAuthorities()
                .iterator().next().getAuthority());
        return buildToken(claims, userDetails,
                appProperties.getJwt().getExpirationMs());
    }

    /**
     * Genera un refresh token de larga duración (7 días).
     * Solo contiene el subject — sin claims adicionales.
     */
    public String generateRefreshToken(UserDetails userDetails) {
        return buildToken(new HashMap<>(), userDetails,
                appProperties.getJwt().getRefreshExpirationMs());
    }

    private String buildToken(Map<String, Object> extraClaims,
                               UserDetails userDetails,
                               long expirationMs) {
        return Jwts.builder()
                .claims(extraClaims)
                .subject(userDetails.getUsername())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationMs))
                .signWith(getSigningKey())
                .compact();
    }

    // ── Validación ────────────────────────────────────────────────────────────

    /**
     * Verifica que el token sea válido para el usuario dado.
     * Comprueba firma, expiración y que el subject coincida con el email.
     */
    public boolean isTokenValid(String token, UserDetails userDetails) {
        try {
            final String email = extractEmail(token);
            return email.equals(userDetails.getUsername()) && !isTokenExpired(token);
        } catch (JwtException | IllegalArgumentException e) {
            log.warn("Token inválido: {}", e.getMessage());
            return false;
        }
    }

    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    // ── Extracción de datos ───────────────────────────────────────────────────

    public String extractEmail(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public String extractRole(String token) {
        return extractClaim(token, claims -> claims.get("role", String.class));
    }

    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    // ── Clave de firma ────────────────────────────────────────────────────────

    private SecretKey getSigningKey() {
        byte[] keyBytes = appProperties.getJwt().getSecret()
                .getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}
