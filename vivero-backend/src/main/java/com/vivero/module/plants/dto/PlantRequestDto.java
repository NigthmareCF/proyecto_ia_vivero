package com.vivero.module.plants.dto;

import com.vivero.shared.enums.PlantState;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO para crear o actualizar plantas.
 */
@Getter
@Setter
public class PlantRequestDto {

    @NotBlank(message = "QR code is required")
    @Size(max = 120, message = "QR code must not exceed 120 characters")
    private String qrCode;

    @NotBlank(message = "Name is required")
    @Size(max = 150, message = "Name must not exceed 150 characters")
    private String name;

    @NotBlank(message = "Location is required")
    @Size(max = 150, message = "Location must not exceed 150 characters")
    private String location;

    @Size(max = 500, message = "Description must not exceed 500 characters")
    private String description;

    @NotNull(message = "Current state is required")
    private PlantState currentState;
}