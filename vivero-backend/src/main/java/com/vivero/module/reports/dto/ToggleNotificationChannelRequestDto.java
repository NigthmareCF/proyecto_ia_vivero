package com.vivero.module.reports.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO para activar o desactivar un canal ya configurado.
 */
@Getter
@Setter
public class ToggleNotificationChannelRequestDto {

    @NotNull(message = "Active flag is required")
    private Boolean active;
}
