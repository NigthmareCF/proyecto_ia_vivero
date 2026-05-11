package com.vivero.module.analisis.controller;

import com.vivero.module.analisis.dto.PlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisResponseDto;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@RestController
@RequestMapping("/analisis")
public class PlantAnalysisController {

    @PostMapping("/planta")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<PlantAnalysisResponseDto>> analyzePlant(
            @Valid @RequestBody PlantAnalysisRequestDto request
    ) {
        String notes = request.getObservacionesOperador() == null
                ? ""
                : request.getObservacionesOperador().trim().toLowerCase(Locale.ROOT);

        String estado = "SANO";
        String urgencia = "BAJA";
        double confianza = 0.74;
        String diagnostico = "No se detectan señales concluyentes de riesgo con la informacion enviada.";
        List<String> hallazgos = new ArrayList<>();
        List<String> recomendaciones = new ArrayList<>();

        if (notes.contains("mancha") || notes.contains("amarill") || notes.contains("seca")) {
            estado = "ATENCION";
            urgencia = "MEDIA";
            confianza = 0.81;
            diagnostico = "Se observan indicios compatibles con estres o afectacion foliar que requieren seguimiento.";
            hallazgos.add("Cambios visuales reportados por el operador en coloracion o textura.");
            hallazgos.add("La evidencia sugiere revisar riego, nutricion y condiciones ambientales.");
            recomendaciones.add("Programar una nueva captura con mejor iluminacion.");
            recomendaciones.add("Verificar riego, drenaje y presencia de plagas en hojas y tallo.");
        }

        if (notes.contains("hongo") || notes.contains("plaga") || notes.contains("necrosis") || notes.contains("pudric")) {
            estado = "PELIGRO";
            urgencia = "ALTA";
            confianza = 0.89;
            diagnostico = "Los indicios descritos son compatibles con una condicion critica que requiere intervencion pronta.";
            hallazgos.clear();
            hallazgos.add("La descripcion del operador coincide con sintomas de afectacion severa.");
            hallazgos.add("Se recomienda aislar el ejemplar y documentar evidencia adicional.");
            recomendaciones.clear();
            recomendaciones.add("Elevar el caso a revision manual inmediata.");
            recomendaciones.add("Tomar nuevas imagenes de hojas, tallo y sustrato para soporte del reporte.");
        }

        if (hallazgos.isEmpty()) {
            hallazgos.add("No se registraron hallazgos criticos en la solicitud actual.");
            recomendaciones.add("Mantener monitoreo periodico en el siguiente patrullaje.");
            recomendaciones.add("Capturar nueva evidencia si aparecen cambios visibles.");
        }

        PlantAnalysisResponseDto response = PlantAnalysisResponseDto.builder()
                .estadoGeneral(estado)
                .urgencia(urgencia)
                .confianza(confianza)
                .diagnostico(diagnostico)
                .hallazgos(hallazgos)
                .recomendaciones(recomendaciones)
                .build();

        return ResponseEntity.ok(ApiResponse.ok("Analisis de planta generado correctamente", response));
    }
}
