package com.vivero.module.analisis.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vivero.module.analisis.dto.PlantAnalysisRequest;
import com.vivero.module.analisis.dto.PlantAnalysisResponse;
import com.vivero.module.analisis.entity.PlantReport;
import com.vivero.module.analisis.repository.PlantReportRepository;
import com.vivero.module.analisis.service.PlantAnalysisService;
import com.vivero.module.analisis.service.vision.VisionApiClient;
import com.vivero.module.analisis.service.vision.VisionDiagnosis;
import com.vivero.shared.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class PlantAnalysisServiceImpl implements PlantAnalysisService {

    private final PlantReportRepository plantReportRepository;
    private final VisionApiClient visionApiClient;
    private final SimpMessagingTemplate messagingTemplate;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional
    public PlantAnalysisResponse analyzePlant(PlantAnalysisRequest request) {
        try {
            VisionDiagnosis diagnosis = visionApiClient.analyzePlantImage(
                    request.getImagenBase64(),
                    request.getMimeType(),
                    request.getObservacionesOperador()
            );

            PlantReport report = PlantReport.builder()
                    .imagenUrl(buildMemoryImageUrl(request.getMimeType()))
                    .observacionesOperador(normalize(request.getObservacionesOperador()))
                    .estadoGeneral(diagnosis.getEstadoGeneral())
                    .confianza(diagnosis.getConfianza())
                    .hallazgos(objectMapper.writeValueAsString(diagnosis.getHallazgos()))
                    .diagnostico(diagnosis.getDiagnostico())
                    .recomendaciones(objectMapper.writeValueAsString(diagnosis.getRecomendaciones()))
                    .urgencia(diagnosis.getUrgencia())
                    .modeloIa(diagnosis.getModeloIa())
                    .build();

            PlantReport savedReport = plantReportRepository.save(report);
            PlantAnalysisResponse response = toResponse(savedReport, diagnosis.getHallazgos(), diagnosis.getRecomendaciones());

            messagingTemplate.convertAndSend("/topic/analisis", response);
            if ("CRITICA".equalsIgnoreCase(response.getUrgencia())) {
                messagingTemplate.convertAndSend("/topic/alertas", response);
            }

            log.info("Analisis de planta generado con id {} y urgencia {}", response.getId(), response.getUrgencia());
            return response;
        } catch (BusinessException ex) {
            throw ex;
        } catch (Exception ex) {
            log.error("Error generating plant analysis", ex);
            throw new BusinessException("Failed to generate plant analysis", "PLANT_ANALYSIS_ERROR");
        }
    }

    private PlantAnalysisResponse toResponse(PlantReport report, List<String> hallazgos, List<String> recomendaciones) {
        return PlantAnalysisResponse.builder()
                .id(report.getId())
                .estadoGeneral(report.getEstadoGeneral())
                .confianza(report.getConfianza())
                .hallazgos(hallazgos)
                .diagnostico(report.getDiagnostico())
                .recomendaciones(recomendaciones)
                .urgencia(report.getUrgencia())
                .modeloIa(report.getModeloIa())
                .createdAt(report.getCreatedAt())
                .build();
    }

    private String buildMemoryImageUrl(String mimeType) {
        String extension = switch (mimeType) {
            case "image/png" -> "png";
            case "image/webp" -> "webp";
            default -> "jpg";
        };
        return "memory://analisis/inline-upload." + extension;
    }

    private String normalize(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }
}
