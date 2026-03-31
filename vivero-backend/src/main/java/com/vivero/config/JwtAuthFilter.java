package com.vivero.config;

import com.vivero.module.auth.util.JwtUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * Filtro que se ejecuta UNA VEZ por cada request HTTP.
 *
 * Flujo:
 * 1. Lee el header Authorization: Bearer <token>
 * 2. Extrae el email del token
 * 3. Carga el usuario de la DB
 * 4. Valida el token (firma + expiración + subject)
 * 5. Si es válido, registra la autenticación en el SecurityContext
 * 6. Spring Security permite el acceso al endpoint protegido
 *
 * Si el token no existe o es inválido, el filtro simplemente
 * continúa sin autenticar — Spring Security devolverá 401.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;
    private final UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(@NonNull HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain)
            throws ServletException, IOException {

        final String authHeader = request.getHeader("Authorization");

        // Si no hay header o no empieza con "Bearer ", pasar al siguiente filtro
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        // Extraer el token eliminando "Bearer " del inicio
        final String token = authHeader.substring(7);
        final String email;

        try {
            email = jwtUtil.extractEmail(token);
        } catch (Exception e) {
            log.warn("No se pudo extraer el email del token: {}", e.getMessage());
            filterChain.doFilter(request, response);
            return;
        }

        // Solo autenticar si hay email y aún no hay autenticación en el contexto
        if (email != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = userDetailsService.loadUserByUsername(email);

            if (jwtUtil.isTokenValid(token, userDetails)) {
                // Crear objeto de autenticación y registrarlo en el SecurityContext
                UsernamePasswordAuthenticationToken authToken =
                        new UsernamePasswordAuthenticationToken(
                                userDetails,
                                null,
                                userDetails.getAuthorities()
                        );
                authToken.setDetails(
                        new WebAuthenticationDetailsSource().buildDetails(request)
                );
                SecurityContextHolder.getContext().setAuthentication(authToken);
                log.debug("Usuario autenticado: {} | endpoint: {}",
                        email, request.getRequestURI());
            }
        }

        filterChain.doFilter(request, response);
    }
}
