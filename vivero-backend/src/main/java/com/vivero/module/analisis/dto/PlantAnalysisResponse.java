package com.vivero.module.analisis.dto;

import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Getter
@Builder
public class PlantAnalysisResponse {

    private UUID id;
    private String estadoGeneral;
    private BigDecimal confianza;
    private List<String> hallazgos;
    private String diagnostico;
    private List<String> recomendaciones;
    private String urgencia;
    private String modeloIa;
    private OffsetDateTime createdAt;
}
