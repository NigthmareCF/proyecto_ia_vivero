package com.vivero.module.users.dto;

import com.vivero.shared.enums.UserRole;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO específico para cambio de rol sin tocar el resto del usuario.
 */
@Getter
@Setter
public class UpdateRoleRequestDto {

    @NotNull(message = "Role is required")
    private UserRole role;
}
