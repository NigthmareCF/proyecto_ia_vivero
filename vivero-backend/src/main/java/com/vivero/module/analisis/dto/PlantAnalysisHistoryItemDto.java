package com.vivero.module.analisis.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Builder
public class PlantAnalysisHistoryItemDto {

    private Long id;
    private String sourceType;
    private String estadoGeneral;
    private String urgencia;
    private double confianza;
    private String summaryText;
    private List<String> hallazgos;
    private List<String> recomendaciones;
    private String modeloIa;
    private String proveedorIa;
    private boolean requiereRevisionManual;
    private boolean fallback;
    private Long patrolId;
    private Long reportId;
    private String reportTitle;
    private String generatedByName;
    private List<String> generalLabels;
    private List<String> exactLabels;
    private List<PlantAnalysisHistoryImageDto> images;
    private LocalDateTime createdAt;
}
