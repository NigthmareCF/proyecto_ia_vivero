package com.vivero.module.reports.mapper;

import com.vivero.module.reports.dto.NotificationConfigDto;
import com.vivero.module.reports.dto.ReportResponseDto;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import org.springframework.stereotype.Component;

/**
 * Mapper manual del módulo reports.
 */
@Component
public class ReportMapper {

    public ReportResponseDto toResponse(Report report) {
        return ReportResponseDto.builder()
                .id(report.getId())
                .patrolId(report.getPatrolId())
                .generatedById(report.getGeneratedBy().getId())
                .generatedByName(report.getGeneratedBy().getFullName())
                .generatedByEmail(report.getGeneratedBy().getEmail())
                .title(report.getTitle())
                .summary(report.getSummary())
                .observationsCount(report.getObservationsCount())
                .healthyCount(report.getHealthyCount())
                .attentionCount(report.getAttentionCount())
                .dangerCount(report.getDangerCount())
                .pdfPath(report.getPdfPath())
                .createdAt(report.getCreatedAt())
                .build();
    }

    public NotificationConfigDto toConfigDto(NotificationConfig config) {
        String contactValue = switch (config.getChannel()) {
            case SMS, WHATSAPP -> config.getUser() == null ? null : config.getUser().getPhoneNumber();
            case EMAIL -> config.getContactValue();
        };
        return NotificationConfigDto.builder()
                .id(config.getId())
                .channel(config.getChannel())
                .contactValue(contactValue)
                .active(config.isActive())
                .build();
    }
}
