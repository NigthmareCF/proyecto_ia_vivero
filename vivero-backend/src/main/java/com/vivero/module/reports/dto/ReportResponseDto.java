package com.vivero.module.reports.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * DTO de salida del módulo reports.
 */
@Getter
@Builder
public class ReportResponseDto {

    private Long id;
    private Long patrolId;
    private Long generatedById;
    private String generatedByName;
    private String generatedByEmail;
    private String title;
    private String summary;
    private Integer observationsCount;
    private Integer healthyCount;
    private Integer attentionCount;
    private Integer dangerCount;
    private String pdfPath;
    private LocalDateTime createdAt;
}
