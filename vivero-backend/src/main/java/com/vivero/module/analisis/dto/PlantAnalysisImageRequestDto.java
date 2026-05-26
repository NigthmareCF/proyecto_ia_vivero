package com.vivero.module.analisis.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PlantAnalysisImageRequestDto {

    @NotBlank
    private String imagenBase64;

    @NotBlank
    private String mimeType;
}
