package com.vivero.module.reports.mapper;

import com.vivero.module.reports.dto.NotificationConfigDto;
import com.vivero.module.reports.dto.ReportPlantDetailDto;
import com.vivero.module.reports.dto.ReportResponseDto;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Mapper manual del módulo reports.
 */
@Component
@RequiredArgsConstructor
public class ReportMapper {

    private final ObjectMapper objectMapper;

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
                .manualReviewCount(report.getManualReviewCount())
                .inconclusiveCount(report.getInconclusiveCount())
                .plantDetails(readPlantDetails(report.getPlantDetailsJson()))
                .pdfPath(report.getPdfPath())
                .createdAt(report.getCreatedAt())
                .build();
    }

    public NotificationConfigDto toConfigDto(NotificationConfig config) {
        return NotificationConfigDto.builder()
                .id(config.getId())
                .channel(config.getChannel())
                .contactValue(config.getContactValue())
                .active(config.isActive())
                .build();
    }

    private List<ReportPlantDetailDto> readPlantDetails(String plantDetailsJson) {
        if (plantDetailsJson == null || plantDetailsJson.isBlank()) {
            return List.of();
        }
        try {
            return objectMapper.readValue(plantDetailsJson, new TypeReference<List<ReportPlantDetailDto>>() { });
        } catch (Exception ex) {
            return List.of();
        }
    }
}
