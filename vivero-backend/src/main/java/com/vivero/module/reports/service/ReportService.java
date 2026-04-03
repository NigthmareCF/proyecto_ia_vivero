package com.vivero.module.reports.service;

import com.vivero.module.reports.dto.GenerateReportRequestDto;
import com.vivero.module.reports.dto.NotificationChannelConfigRequestDto;
import com.vivero.module.reports.dto.NotificationConfigDto;
import com.vivero.module.reports.dto.NotifyReportRequestDto;
import com.vivero.module.reports.dto.ReportResponseDto;
import com.vivero.shared.enums.NotificationChannel;

import java.util.List;

/**
 * Contrato del módulo de reportes.
 */
public interface ReportService {

    List<ReportResponseDto> getAllReports();

    ReportResponseDto getReportById(Long id);

    ReportResponseDto generateReport(GenerateReportRequestDto request, String currentUserEmail);

    byte[] getReportPdf(Long id);

    List<NotificationConfigDto> getNotificationConfigs(String currentUserEmail);

    List<NotificationConfigDto> saveNotificationConfigs(List<NotificationConfigDto> request, String currentUserEmail);

    NotificationConfigDto saveNotificationConfig(
            NotificationChannel channel,
            NotificationChannelConfigRequestDto request,
            String currentUserEmail
    );

    NotificationConfigDto toggleNotificationChannel(
            NotificationChannel channel,
            boolean active,
            String currentUserEmail
    );

    List<NotificationChannel> getSupportedNotificationChannels();

    int notifyReport(NotifyReportRequestDto request, String currentUserEmail);
}
