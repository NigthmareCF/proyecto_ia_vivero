package com.vivero.module.analisis.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;

@Getter
@Setter
public class ManualPlantAnalysisRequestDto {

    @Valid
    @NotEmpty
    private List<PlantAnalysisImageRequestDto> images = new ArrayList<>();

    private List<String> generalLabels = new ArrayList<>();

    private List<String> exactLabels = new ArrayList<>();

    @NotBlank
    private String estadoGeneral;

    @NotBlank
    private String urgencia;

    @NotBlank
    private String reporteManual;

    @DecimalMin("0.0")
    @DecimalMax("1.0")
    private Double confianza;

    private List<String> hallazgos = new ArrayList<>();

    private List<String> recomendaciones = new ArrayList<>();

    private String operatorNotes;

    private Long patrolId;

    private Boolean createStandaloneReport;

    private String reportTitle;
}
