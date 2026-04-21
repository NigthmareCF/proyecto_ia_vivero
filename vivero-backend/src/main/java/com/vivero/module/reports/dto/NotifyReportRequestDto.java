package com.vivero.module.reports.dto;

import com.vivero.shared.enums.NotificationChannel;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * DTO de entrada para el envío manual de notificaciones de un reporte.
 */
@Getter
@Setter
public class NotifyReportRequestDto {

    @NotNull(message = "Report ID is required")
    private Long reportId;

    private List<NotificationChannel> channels;
}
