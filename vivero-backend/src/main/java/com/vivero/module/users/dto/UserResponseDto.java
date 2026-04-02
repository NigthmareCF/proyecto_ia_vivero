package com.vivero.module.users.dto;

import com.vivero.shared.enums.UserRole;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * DTO de salida para exponer datos de usuario sin incluir la contraseña.
 */
@Getter
@Builder
public class UserResponseDto {

    private Long id;
    private String firstName;
    private String lastName;
    private String fullName;
    private String email;
    private UserRole role;
    private boolean active;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
