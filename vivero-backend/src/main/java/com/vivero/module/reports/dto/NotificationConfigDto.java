package com.vivero.module.reports.dto;

import com.vivero.shared.enums.NotificationChannel;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO de entrada y salida para la configuración de notificaciones.
 */
@Getter
@Setter
@Builder
public class NotificationConfigDto {

    private Long id;

    @NotNull(message = "Channel is required")
    private NotificationChannel channel;

    @NotBlank(message = "Contact value is required")
    @Size(max = 255, message = "Contact value must not exceed 255 characters")
    private String contactValue;

    @Builder.Default
    private Boolean active = Boolean.TRUE;
}
