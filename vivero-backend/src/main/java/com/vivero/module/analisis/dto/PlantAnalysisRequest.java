package com.vivero.module.analisis.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PlantAnalysisRequest {

    @NotBlank(message = "La imagen en base64 es obligatoria")
    private String imagenBase64;

    @NotBlank(message = "El mimeType es obligatorio")
    private String mimeType;

    private String observacionesOperador;
}
