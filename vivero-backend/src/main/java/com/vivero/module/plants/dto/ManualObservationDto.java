package com.vivero.module.plants.dto;

import com.vivero.shared.enums.PlantState;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO reservado para observaciones manuales desde frontend.
 * La persistencia detallada se integrará con el módulo patrols/observations.
 */
@Getter
@Setter
public class ManualObservationDto {

    @NotBlank(message = "Operator notes are required")
    @Size(max = 500, message = "Operator notes must not exceed 500 characters")
    private String operatorNotes;

    @Size(max = 255, message = "Manual causes must not exceed 255 characters")
    private String manualCauses;

    @NotNull(message = "Observed state is required")
    private PlantState observedState;
}