package com.vivero.module.analisis.dto;

import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
public class PlantAnalysisResponseDto {

    private String estadoGeneral;
    private String urgencia;
    private double confianza;
    private String diagnostico;
    private List<String> hallazgos;
    private List<String> recomendaciones;
}
