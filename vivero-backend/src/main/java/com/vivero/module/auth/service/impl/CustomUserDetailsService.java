package com.vivero.module.auth.service.impl;

import com.vivero.module.auth.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

/**
 * Implementación de UserDetailsService requerida por Spring Security.
 *
 * Spring Security llama a loadUserByUsername() en dos momentos:
 * 1. Durante el login — AuthenticationManager lo usa para verificar credenciales
 * 2. Durante cada request — JwtAuthFilter lo usa para cargar el usuario del token
 *
 * Se mantiene separado de AuthServiceImpl para evitar dependencias circulares:
 * SecurityConfig → UserDetailsService → UserRepository  (sin ciclo)
 * SecurityConfig → AuthenticationManager → UserDetailsService (sin ciclo)
 */
@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    /**
     * Carga el usuario por email (username en el contexto de Spring Security).
     * La entidad User implementa UserDetails, por lo que se devuelve directamente.
     */
    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException(
                        "User not found with email: " + email));
    }
}
