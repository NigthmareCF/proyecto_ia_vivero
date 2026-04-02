package com.vivero.module.plants.dto;

import com.vivero.shared.enums.PlantState;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * DTO de salida del módulo plants.
 */
@Getter
@Builder
public class PlantResponseDto {

    private Long id;
    private String qrCode;
    private String name;
    private String location;
    private String description;
    private PlantState currentState;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}