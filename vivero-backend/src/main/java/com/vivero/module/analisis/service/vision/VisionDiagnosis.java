package com.vivero.module.analisis.service.vision;

import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.util.List;

@Getter
@Builder
public class VisionDiagnosis {

    private String estadoGeneral;
    private BigDecimal confianza;
    private List<String> hallazgos;
    private String diagnostico;
    private List<String> recomendaciones;
    private String urgencia;
    private String modeloIa;
}
