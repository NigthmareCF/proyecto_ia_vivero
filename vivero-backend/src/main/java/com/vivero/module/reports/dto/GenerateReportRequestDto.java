package com.vivero.module.reports.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO de entrada para generar un reporte PDF persistente.
 */
@Getter
@Setter
public class GenerateReportRequestDto {

    @NotNull(message = "Patrol ID is required")
    private Long patrolId;

    @NotBlank(message = "Title is required")
    @Size(max = 150, message = "Title must not exceed 150 characters")
    private String title;

    @Size(max = 1000, message = "Summary must not exceed 1000 characters")
    private String summary;

    @NotNull(message = "Observations count is required")
    @Min(value = 0, message = "Observations count must be zero or greater")
    private Integer observationsCount;

    @NotNull(message = "Healthy count is required")
    @Min(value = 0, message = "Healthy count must be zero or greater")
    private Integer healthyCount;

    @NotNull(message = "Attention count is required")
    @Min(value = 0, message = "Attention count must be zero or greater")
    private Integer attentionCount;

    @NotNull(message = "Danger count is required")
    @Min(value = 0, message = "Danger count must be zero or greater")
    private Integer dangerCount;
}
