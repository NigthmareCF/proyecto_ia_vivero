package com.vivero.module.reports.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO para configurar un canal específico de notificación.
 */
@Getter
@Setter
public class NotificationChannelConfigRequestDto {

    @NotBlank(message = "Contact value is required")
    @Size(max = 255, message = "Contact value must not exceed 255 characters")
    private String contactValue;

    private Boolean active = Boolean.TRUE;
}
