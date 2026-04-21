package com.vivero.module.auth.entity;

import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.UserRole;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;

/**
 * Entidad principal de usuario del sistema.
 * Implementa UserDetails para integrarse directamente con Spring Security.
 *
 * La tabla 'users' almacena:
 * - Credenciales de acceso (email + password encriptado con BCrypt)
 * - Rol que determina los permisos en la API y la interfaz
 * - Estado activo/inactivo para deshabilitar usuarios sin borrarlos
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "users")
public class User extends BaseEntity implements UserDetails {

    @Column(nullable = false)
    private String firstName;

    @Column(nullable = false)
    private String lastName;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(name = "phone_number", length = 20)
    private String phoneNumber;

    @Column(nullable = false)
    private String password;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserRole role;

    // Si es false, el usuario existe pero no puede iniciar sesión
    @Builder.Default
    @Column(nullable = false)
    private boolean active = true;

    // ── Implementación de UserDetails (requerida por Spring Security) ──────────

    /**
     * Convierte el rol en una GrantedAuthority con prefijo ROLE_.
     * Spring Security usa este prefijo para las anotaciones @PreAuthorize("hasRole(...)")
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_" + role.name()));
    }

    // Spring Security usa el email como nombre de usuario
    @Override
    public String getUsername() {
        return email;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return active;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return active;
    }

    // Nombre completo para mostrar en la interfaz y los reportes
    public String getFullName() {
        return firstName + " " + lastName;
    }
}
