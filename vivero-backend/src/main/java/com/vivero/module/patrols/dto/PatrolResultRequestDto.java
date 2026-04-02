package com.vivero.module.patrols.dto;

import com.vivero.shared.enums.PlantState;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO que representa un resultado individual enviado por el robot.
 */
@Getter
@Setter
public class PatrolResultRequestDto {

    @NotBlank(message = "Plant QR code is required")
    @Size(max = 120, message = "Plant QR code must not exceed 120 characters")
    private String plantQrCode;

    @NotNull(message = "AI result is required")
    private PlantState aiResult;

    @NotNull(message = "AI confidence is required")
    @DecimalMin(value = "0.0", message = "AI confidence must be at least 0.0")
    @DecimalMax(value = "1.0", message = "AI confidence must be at most 1.0")
    private Double aiConfidence;

    @Size(max = 255, message = "Manual causes must not exceed 255 characters")
    private String manualCauses;

    @Size(max = 500, message = "Operator notes must not exceed 500 characters")
    private String operatorNotes;

    @Size(max = 2000, message = "Image paths must not exceed 2000 characters")
    private String imagePaths;
}