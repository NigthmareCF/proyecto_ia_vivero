package com.vivero.module.auth.service.oauth;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSVerifier;
import com.nimbusds.jose.crypto.RSASSAVerifier;
import com.nimbusds.jwt.SignedJWT;
import com.vivero.config.AppProperties;
import com.vivero.shared.enums.AuthProvider;
import com.vivero.shared.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.security.interfaces.RSAPublicKey;
import java.text.ParseException;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

@Service
@RequiredArgsConstructor
public class OidcSocialTokenVerifier implements SocialTokenVerifier {

    private final AppProperties appProperties;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    @Override
    public SocialIdentityProfile verify(AuthProvider provider, String idToken) {
        if (provider == AuthProvider.LOCAL) {
            throw new BusinessException("LOCAL is not a social provider", "INVALID_SOCIAL_PROVIDER");
        }

        SignedJWT jwt = parseToken(idToken);
        AppProperties.Oauth.Provider providerConfig = resolveProviderConfig(provider);
        JsonNode jwkNode = resolveMatchingKey(providerConfig.getJwksUri(), jwt.getHeader().getKeyID());

        try {
            RSAPublicKey publicKey = (RSAPublicKey) com.nimbusds.jose.jwk.RSAKey
                    .parse(jwkNode.toString())
                    .toRSAPublicKey();
            JWSVerifier verifier = new RSASSAVerifier(publicKey);
            if (!jwt.verify(verifier)) {
                throw new BusinessException("Invalid social token signature", "INVALID_SOCIAL_TOKEN");
            }
        } catch (JOSEException | ParseException ex) {
            throw new BusinessException("Failed to verify social token", "INVALID_SOCIAL_TOKEN");
        }

        return extractProfile(provider, providerConfig, jwt);
    }

    private SignedJWT parseToken(String idToken) {
        try {
            return SignedJWT.parse(idToken);
        } catch (ParseException ex) {
            throw new BusinessException("Invalid social token format", "INVALID_SOCIAL_TOKEN");
        }
    }

    private AppProperties.Oauth.Provider resolveProviderConfig(AuthProvider provider) {
        AppProperties.Oauth.Provider config = provider == AuthProvider.GOOGLE
                ? appProperties.getOauth().getGoogle()
                : appProperties.getOauth().getApple();

        if (isBlank(config.getClientId()) || isBlank(config.getIssuer()) || isBlank(config.getJwksUri())) {
            throw new BusinessException(
                    "OAuth provider configuration is incomplete for " + provider,
                    "OAUTH_PROVIDER_NOT_CONFIGURED"
            );
        }
        return config;
    }

    private JsonNode resolveMatchingKey(String jwksUri, String keyId) {
        if (isBlank(keyId)) {
            throw new BusinessException("Social token does not contain key id", "INVALID_SOCIAL_TOKEN");
        }

        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(jwksUri))
                    .timeout(Duration.ofSeconds(10))
                    .GET()
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() >= 400) {
                throw new BusinessException("Unable to fetch provider keys", "OAUTH_PROVIDER_UNAVAILABLE");
            }

            JsonNode root = objectMapper.readTree(response.body());
            for (JsonNode keyNode : root.path("keys")) {
                if (keyId.equals(keyNode.path("kid").asText())) {
                    return keyNode;
                }
            }
        } catch (IOException ex) {
            throw new BusinessException("Unable to parse provider keys", "OAUTH_PROVIDER_UNAVAILABLE");
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new BusinessException("Provider key request was interrupted", "OAUTH_PROVIDER_UNAVAILABLE");
        }

        throw new BusinessException("Matching provider key was not found", "INVALID_SOCIAL_TOKEN");
    }

    private SocialIdentityProfile extractProfile(
            AuthProvider provider,
            AppProperties.Oauth.Provider providerConfig,
            SignedJWT jwt
    ) {
        try {
            var claims = jwt.getJWTClaimsSet();

            if (!providerConfig.getIssuer().equals(claims.getIssuer())) {
                throw new BusinessException("Invalid token issuer", "INVALID_SOCIAL_TOKEN");
            }
            if (claims.getAudience() == null || !claims.getAudience().contains(providerConfig.getClientId())) {
                throw new BusinessException("Invalid token audience", "INVALID_SOCIAL_TOKEN");
            }

            Date expirationTime = claims.getExpirationTime();
            if (expirationTime == null || expirationTime.toInstant().isBefore(Instant.now())) {
                throw new BusinessException("Social token has expired", "INVALID_SOCIAL_TOKEN");
            }

            String email = claims.getStringClaim("email");
            if (isBlank(email)) {
                throw new BusinessException("Social token does not contain an email", "SOCIAL_EMAIL_REQUIRED");
            }

            String subject = claims.getSubject();
            if (isBlank(subject)) {
                throw new BusinessException("Social token does not contain a subject", "INVALID_SOCIAL_TOKEN");
            }

            String givenName = normalize(claims.getStringClaim("given_name"));
            String familyName = normalize(claims.getStringClaim("family_name"));
            String fullName = normalize(claims.getStringClaim("name"));
            if (isBlank(fullName)) {
                fullName = (givenName + " " + familyName).trim();
            }
            if (isBlank(givenName) && !isBlank(fullName)) {
                givenName = fullName;
            }
            if (isBlank(familyName)) {
                familyName = provider.name();
            }

            Object verifiedClaim = claims.getClaim("email_verified");
            boolean emailVerified = verifiedClaim instanceof Boolean booleanClaim
                    ? booleanClaim
                    : Boolean.parseBoolean(String.valueOf(verifiedClaim));

            return SocialIdentityProfile.builder()
                    .provider(provider)
                    .providerUserId(subject)
                    .email(email.toLowerCase().trim())
                    .emailVerified(emailVerified)
                    .firstName(givenName)
                    .lastName(familyName)
                    .fullName(fullName)
                    .avatarUrl(claims.getStringClaim("picture"))
                    .build();
        } catch (ParseException ex) {
            throw new BusinessException("Unable to parse social token claims", "INVALID_SOCIAL_TOKEN");
        }
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim();
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
