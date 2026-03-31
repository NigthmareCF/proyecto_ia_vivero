package com.vivero.module.auth.repository;

import com.vivero.module.auth.entity.User;
import com.vivero.shared.enums.UserRole;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repositorio JPA para la entidad User.
 * Spring Data genera automáticamente la implementación SQL en runtime.
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    // Búsqueda por email — usada por Spring Security en el login
    Optional<User> findByEmail(String email);

    // Verificación de email único antes de registrar un nuevo usuario
    boolean existsByEmail(String email);

    // Filtrar usuarios por rol — usado en la pantalla de gestión de usuarios
    List<User> findByRole(UserRole role);

    // Filtrar usuarios activos/inactivos
    List<User> findByActive(boolean active);
}
