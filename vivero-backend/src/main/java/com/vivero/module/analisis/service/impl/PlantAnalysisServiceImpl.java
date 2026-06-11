package com.vivero.module.analisis.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vivero.config.VisionApiProperties;
import com.vivero.module.analisis.dto.ManualPlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisHistoryImageDto;
import com.vivero.module.analisis.dto.PlantAnalysisHistoryItemDto;
import com.vivero.module.analisis.dto.PlantAnalysisImageRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisResponseDto;
import com.vivero.module.analisis.entity.PlantAnalysisRecord;
import com.vivero.module.analisis.entity.PlantAnalysisRecordImage;
import com.vivero.module.analisis.repository.PlantAnalysisRecordImageRepository;
import com.vivero.module.analisis.repository.PlantAnalysisRecordRepository;
import com.vivero.module.analisis.service.PlantAnalysisService;
import com.vivero.module.analisis.service.support.PlantAnalysisImageStorageService;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.reports.dto.ReportFindingDto;
import com.vivero.module.reports.dto.ReportPlantDetailDto;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.pdf.PdfReportGenerator;
import com.vivero.module.reports.repository.ReportRepository;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class PlantAnalysisServiceImpl implements PlantAnalysisService {

    private static final List<String> ALLOWED_STATES = List.of("SANO", "ATENCION", "PELIGRO", "REVISION_MANUAL");
    private static final List<String> ALLOWED_URGENCY = List.of("BAJA", "MEDIA", "ALTA", "CRITICA");
    private static final List<String> ALLOWED_SOURCE_TYPES = List.of("MANUAL", "AI_ASSISTED");

    private final VisionApiProperties visionApiProperties;
    private final ObjectMapper objectMapper;
    private final SimpMessagingTemplate messagingTemplate;
    private final PlantAnalysisRecordRepository plantAnalysisRecordRepository;
    private final PlantAnalysisRecordImageRepository plantAnalysisRecordImageRepository;
    private final PlantAnalysisImageStorageService plantAnalysisImageStorageService;
    private final UserRepository userRepository;
    private final ReportRepository reportRepository;
    private final PdfReportGenerator pdfReportGenerator;

    @Override
    @Transactional
    public PlantAnalysisResponseDto analyzePlant(PlantAnalysisRequestDto request, String currentUserEmail) {
        PlantAnalysisResponseDto response = resolveAnalysis(request);
        User currentUser = findUserOrThrow(currentUserEmail);
        persistAiAnalysis(request, response, currentUser);
        messagingTemplate.convertAndSend("/topic/analisis", response);
        if ("ALTA".equals(response.getUrgencia()) || "CRITICA".equals(response.getUrgencia())) {
            messagingTemplate.convertAndSend("/topic/alertas", response);
        }
        return response;
    }

    @Override
    @Transactional
    public PlantAnalysisHistoryItemDto createManualAnalysis(ManualPlantAnalysisRequestDto request, String currentUserEmail) {
        validateManualAnalysisRequest(request);
        User currentUser = findUserOrThrow(currentUserEmail);

        List<String> generalLabels = normalizeLabels(request.getGeneralLabels());
        List<String> exactLabels = normalizeLabels(request.getExactLabels());
        String estado = normalizeChoice(request.getEstadoGeneral(), ALLOWED_STATES, "REVISION_MANUAL");
        String urgencia = normalizeChoice(request.getUrgencia(), ALLOWED_URGENCY, "MEDIA");

        PlantAnalysisRecord analysisRecord = PlantAnalysisRecord.builder()
                .generatedBy(currentUser)
                .sourceType("MANUAL")
                .estadoGeneral(estado)
                .urgencia(urgencia)
                .confianza(request.getConfianza() == null ? 1.0 : clamp(request.getConfianza()))
                .summaryText(request.getReporteManual().trim())
                .hallazgosJson(writeStringArray(normalizeLabels(request.getHallazgos())))
                .recomendacionesJson(writeStringArray(normalizeLabels(request.getRecomendaciones())))
                .operatorNotes(normalizeText(request.getOperatorNotes()))
                .generalLabelsJson(writeStringArray(generalLabels))
                .exactLabelsJson(writeStringArray(exactLabels))
                .primaryGeneralLabel(generalLabels.isEmpty() ? null : generalLabels.get(0))
                .primaryExactLabel(exactLabels.isEmpty() ? null : exactLabels.get(0))
                .patrolId(request.getPatrolId())
                .reportId(null)
                .reportTitleSnapshot(null)
                .modeloIa(null)
                .proveedorIa("manual")
                .requiereRevisionManual("REVISION_MANUAL".equals(estado))
                .fallback(false)
                .build();

        plantAnalysisRecordRepository.save(analysisRecord);
        storeAnalysisImages(analysisRecord, request.getImages());

        if (Boolean.TRUE.equals(request.getCreateStandaloneReport())) {
            Report report = createStandaloneManualReport(analysisRecord, request, currentUser, exactLabels, generalLabels);
            analysisRecord.setReportId(report.getId());
            analysisRecord.setReportTitleSnapshot(report.getTitle());
            plantAnalysisRecordRepository.save(analysisRecord);
        }

        return toHistoryItem(analysisRecord);
    }

    @Override
    @Transactional(readOnly = true)
    public List<PlantAnalysisHistoryItemDto> getAnalysisHistory() {
        return plantAnalysisRecordRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(this::toHistoryItem)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public StoredAnalysisImage getAnalysisImage(Long imageId) {
        PlantAnalysisRecordImage image = plantAnalysisRecordImageRepository.findById(imageId)
                .orElseThrow(() -> new ResourceNotFoundException("Analysis image not found with id: " + imageId));
        try {
            return new StoredAnalysisImage(image.getMimeType(), Files.readAllBytes(Path.of(image.getFilePath())));
        } catch (IOException ex) {
            throw new ResourceNotFoundException("Analysis image file is missing for id: " + imageId);
        }
    }

    private PlantAnalysisResponseDto resolveAnalysis(PlantAnalysisRequestDto request) {
        if (!isGeminiEnabled()) {
            return buildFallbackAnalysis(request, "Vision API desactivada o sin credenciales.");
        }

        try {
            return callGemini(request);
        } catch (Exception exception) {
            log.warn("Fallo el analisis con Gemini, se usa fallback local: {}", exception.getMessage());
            return buildFallbackAnalysis(request, "Fallo al invocar Gemini API.");
        }
    }

    private boolean isGeminiEnabled() {
        return visionApiProperties.isEnabled()
                && "gemini".equalsIgnoreCase(visionApiProperties.getProvider())
                && visionApiProperties.getGemini().getKey() != null
                && !visionApiProperties.getGemini().getKey().isBlank();
    }

    private PlantAnalysisResponseDto callGemini(PlantAnalysisRequestDto request) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(visionApiProperties.getTimeoutSeconds()))
                .build();

        String prompt = """
                Analiza esta imagen de una planta de chile pimiento en vivero y responde SOLO JSON valido.
                Basa tu conclusion principalmente en la evidencia visual observable y usa las observaciones del operador solo como contexto secundario.

                Objetivo del diagnostico:
                - no responder demasiado largo
                - pero si ser especifico, claro y util para operacion
                - explicar por que tomas la decision
                - indicar que signos se ven mas marcados
                - mencionar posibles causas probables solo si son consistentes con lo visible

                Reglas:
                - estadoGeneral debe ser uno de: SANO, ATENCION, PELIGRO, REVISION_MANUAL
                - urgencia debe ser una de: BAJA, MEDIA, ALTA, CRITICA
                - confianza debe estar entre 0 y 1
                - diagnostico debe tener entre 3 y 4 frases cortas o lineas breves, con tono tecnico y entendible
                - diagnostico debe incluir: conclusion principal, evidencia visual mas relevante, por que esa evidencia soporta el estado elegido y posibles causas probables si aplica
                - hallazgos debe tener entre 2 y 5 elementos concretos basados en lo visible
                - recomendaciones debe tener entre 2 y 5 elementos accionables
                - requiereRevisionManual debe ser true si la imagen no permite una conclusion confiable, si faltan detalles visuales clave o si hay ambiguedad
                - si la evidencia visual no alcanza para afirmar una causa, dilo explicitamente y pide revision manual
                - no inventes datos, sintomas ni causas que no esten respaldados por la imagen
                - evita frases vacias o genericas como "requiere atencion" sin explicar por que

                Observaciones del operador:
                %s
                """.formatted(normalizeOperatorNotes(request.getObservacionesOperador()));

        Map<String, Object> body = Map.of(
                "contents", List.of(
                        Map.of(
                                "parts", List.of(
                                        Map.of("text", prompt),
                                        Map.of("inline_data", Map.of(
                                                "mime_type", request.getMimeType(),
                                                "data", request.getImagenBase64()
                                        ))
                                )
                        )
                ),
                "generationConfig", Map.of(
                        "temperature", 0.2,
                        "responseMimeType", "application/json",
                        "responseSchema", buildGeminiResponseSchema()
                )
        );

        String endpoint = "%s/%s:generateContent"
                .formatted(trimTrailingSlash(visionApiProperties.getGemini().getUrl()), visionApiProperties.getModel());

        HttpRequest httpRequest = HttpRequest.newBuilder()
                .uri(URI.create(endpoint))
                .timeout(Duration.ofSeconds(visionApiProperties.getTimeoutSeconds()))
                .header("Content-Type", "application/json")
                .header("x-goog-api-key", visionApiProperties.getGemini().getKey())
                .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(body)))
                .build();

        HttpResponse<String> httpResponse = client.send(httpRequest, HttpResponse.BodyHandlers.ofString());
        if (httpResponse.statusCode() < 200 || httpResponse.statusCode() >= 300) {
            throw new IOException("Gemini devolvio HTTP " + httpResponse.statusCode());
        }

        JsonNode root = objectMapper.readTree(httpResponse.body());
        String textPayload = extractGeminiText(root);
        if (textPayload == null || textPayload.isBlank()) {
            throw new IOException("Gemini no devolvio contenido interpretable.");
        }

        return normalizeModelResponse(objectMapper.readTree(textPayload));
    }

    private PlantAnalysisResponseDto normalizeModelResponse(JsonNode parsed) {
        String estado = normalizeChoice(parsed.path("estadoGeneral").asText(null), ALLOWED_STATES, "REVISION_MANUAL");
        String urgencia = normalizeChoice(parsed.path("urgencia").asText(null), ALLOWED_URGENCY, "MEDIA");
        boolean requiereRevisionManual = parsed.path("requiereRevisionManual").asBoolean(false);

        if (requiereRevisionManual && "SANO".equals(estado)) {
            estado = "REVISION_MANUAL";
        }
        if (requiereRevisionManual && "BAJA".equals(urgencia)) {
            urgencia = "MEDIA";
        }

        List<String> hallazgos = readStringArray(parsed.path("hallazgos"));
        if (hallazgos.isEmpty()) {
            hallazgos = List.of("El proveedor externo no devolvio hallazgos suficientes.");
        }

        List<String> recomendaciones = readStringArray(parsed.path("recomendaciones"));
        if (recomendaciones.isEmpty()) {
            recomendaciones = List.of("Solicitar nueva captura con mejor iluminacion y encuadre.");
        }

        String diagnostico = parsed.path("diagnostico").asText("").trim();
        if (diagnostico.isBlank()) {
            diagnostico = "Analisis completado sin diagnostico textual utilizable.";
        }

        return PlantAnalysisResponseDto.builder()
                .estadoGeneral(estado)
                .urgencia(urgencia)
                .confianza(clamp(parsed.path("confianza").asDouble(0.55)))
                .diagnostico(diagnostico)
                .hallazgos(hallazgos)
                .recomendaciones(recomendaciones)
                .modeloIa(visionApiProperties.getModel())
                .proveedorIa("gemini")
                .requiereRevisionManual(requiereRevisionManual || "REVISION_MANUAL".equals(estado))
                .fallback(false)
                .build();
    }

    private PlantAnalysisResponseDto buildFallbackAnalysis(PlantAnalysisRequestDto request, String reason) {
        String notes = normalizeOperatorNotes(request.getObservacionesOperador()).toLowerCase(Locale.ROOT);

        String estado = "REVISION_MANUAL";
        String urgencia = "MEDIA";
        double confianza = 0.45;
        String diagnostico = "No fue posible completar el analisis visual con el proveedor externo. Se devuelve una evaluacion conservadora.";
        List<String> hallazgos = new ArrayList<>();
        List<String> recomendaciones = new ArrayList<>();

        if (notes.contains("hongo") || notes.contains("plaga") || notes.contains("necrosis") || notes.contains("pudric")) {
            estado = "PELIGRO";
            urgencia = "ALTA";
            confianza = 0.72;
            diagnostico = "Las observaciones del operador mencionan sintomas severos compatibles con una condicion critica.";
            hallazgos.add("Se detectaron palabras clave asociadas a afectacion severa en las observaciones del operador.");
            hallazgos.add("No hubo confirmacion visual automatica, por lo que se recomienda validar con nueva evidencia.");
            recomendaciones.add("Aislar la planta y revisar hojas, tallo y sustrato.");
            recomendaciones.add("Capturar nuevas imagenes detalladas y solicitar revision manual.");
        } else if (notes.contains("mancha") || notes.contains("amarill") || notes.contains("seca")) {
            estado = "ATENCION";
            urgencia = "MEDIA";
            confianza = 0.65;
            diagnostico = "Las observaciones del operador sugieren estres o afectacion foliar que requiere seguimiento.";
            hallazgos.add("Se reportaron cambios de coloracion o textura en la planta.");
            hallazgos.add("El analisis visual externo no estuvo disponible para confirmar el hallazgo.");
            recomendaciones.add("Repetir la captura con mejor iluminacion y mayor cercania.");
            recomendaciones.add("Revisar riego, nutricion y presencia de plagas.");
        } else {
            hallazgos.add("No hubo respuesta utilizable del proveedor externo.");
            hallazgos.add("Sin evidencia visual validada, el caso se marca para revision conservadora.");
            recomendaciones.add("Reintentar el analisis cuando la Vision API este activa.");
            recomendaciones.add("Registrar nuevas observaciones del operador si aparecen sintomas.");
        }

        hallazgos.add("Motivo tecnico: " + reason);

        return PlantAnalysisResponseDto.builder()
                .estadoGeneral(estado)
                .urgencia(urgencia)
                .confianza(confianza)
                .diagnostico(diagnostico)
                .hallazgos(hallazgos)
                .recomendaciones(recomendaciones)
                .modeloIa("fallback-local")
                .proveedorIa("local")
                .requiereRevisionManual(!"PELIGRO".equals(estado))
                .fallback(true)
                .build();
    }

    private void persistAiAnalysis(PlantAnalysisRequestDto request, PlantAnalysisResponseDto response, User currentUser) {
        PlantAnalysisRecord analysisRecord = PlantAnalysisRecord.builder()
                .generatedBy(currentUser)
                .sourceType("AI_ASSISTED")
                .estadoGeneral(response.getEstadoGeneral())
                .urgencia(response.getUrgencia())
                .confianza(response.getConfianza())
                .summaryText(response.getDiagnostico())
                .hallazgosJson(writeStringArray(response.getHallazgos()))
                .recomendacionesJson(writeStringArray(response.getRecomendaciones()))
                .operatorNotes(normalizeText(request.getObservacionesOperador()))
                .generalLabelsJson(writeStringArray(List.of()))
                .exactLabelsJson(writeStringArray(List.of()))
                .primaryGeneralLabel(null)
                .primaryExactLabel(null)
                .patrolId(null)
                .reportId(null)
                .reportTitleSnapshot(null)
                .modeloIa(response.getModeloIa())
                .proveedorIa(response.getProveedorIa())
                .requiereRevisionManual(response.isRequiereRevisionManual())
                .fallback(response.isFallback())
                .build();

        plantAnalysisRecordRepository.save(analysisRecord);
        storeAnalysisImages(
                analysisRecord,
                List.of(PlantAnalysisImageRequestDtoBuilder.of(request.getImagenBase64(), request.getMimeType()))
        );
    }

    private void validateManualAnalysisRequest(ManualPlantAnalysisRequestDto request) {
        if (request.getImages() == null || request.getImages().isEmpty()) {
            throw new BusinessException("At least one image is required", "ANALYSIS_IMAGES_REQUIRED");
        }
        if (normalizeLabels(request.getGeneralLabels()).isEmpty() && normalizeLabels(request.getExactLabels()).isEmpty()) {
            throw new BusinessException("At least one general or exact label is required", "ANALYSIS_LABELS_REQUIRED");
        }
    }

    private void storeAnalysisImages(PlantAnalysisRecord analysisRecord, List<PlantAnalysisImageRequestDto> images) {
        List<String> imagesBase64 = images.stream().map(PlantAnalysisImageRequestDto::getImagenBase64).toList();
        List<String> mimeTypes = images.stream().map(PlantAnalysisImageRequestDto::getMimeType).toList();
        List<PlantAnalysisImageStorageService.StoredAnalysisImage> storedImages =
                plantAnalysisImageStorageService.storeImages(imagesBase64, mimeTypes);

        List<PlantAnalysisRecordImage> entities = storedImages.stream()
                .map(image -> PlantAnalysisRecordImage.builder()
                        .analysisRecord(analysisRecord)
                        .filePath(image.filePath())
                        .mimeType(image.mimeType())
                        .sortOrder(image.sortOrder())
                        .build())
                .toList();

        plantAnalysisRecordImageRepository.saveAll(entities);
    }

    private Report createStandaloneManualReport(
            PlantAnalysisRecord analysisRecord,
            ManualPlantAnalysisRequestDto request,
            User currentUser,
            List<String> exactLabels,
            List<String> generalLabels
    ) {
        List<String> targetLabels = !exactLabels.isEmpty() ? exactLabels : generalLabels;
        int observationsCount = Math.max(1, targetLabels.size());

        List<ReportPlantDetailDto> plantDetails = targetLabels.stream()
                .map(label -> buildReportPlantDetail(label, analysisRecord.getEstadoGeneral(), request.getReporteManual()))
                .toList();

        Report report = Report.builder()
                .patrolId(null)
                .generatedBy(currentUser)
                .title(normalizeText(request.getReportTitle()) == null ? "Analisis manual" : normalizeText(request.getReportTitle()))
                .summary(normalizeText(request.getReporteManual()))
                .observationsCount(observationsCount)
                .healthyCount("SANO".equals(analysisRecord.getEstadoGeneral()) ? observationsCount : 0)
                .attentionCount("ATENCION".equals(analysisRecord.getEstadoGeneral()) ? observationsCount : 0)
                .dangerCount("PELIGRO".equals(analysisRecord.getEstadoGeneral()) ? observationsCount : 0)
                .manualReviewCount("REVISION_MANUAL".equals(analysisRecord.getEstadoGeneral()) ? observationsCount : 0)
                .inconclusiveCount(0)
                .plantDetailsJson(writeReportPlantDetails(plantDetails))
                .analysisProvider(normalizeAnalysisProvider(analysisRecord.getProveedorIa()))
                .analysisModel(normalizeText(analysisRecord.getModeloIa()))
                .analysisNotes(buildAnalysisNotes(analysisRecord))
                .publicShareToken(UUID.randomUUID().toString().replace("-", ""))
                .build();

        reportRepository.save(report);
        if (report.getTitle() == null || report.getTitle().isBlank()) {
            report.setTitle("Analisis manual No. " + report.getId());
        }
        report.setPdfPath(pdfReportGenerator.generateAndStore(report));
        reportRepository.save(report);
        return report;
    }

    private ReportPlantDetailDto buildReportPlantDetail(String label, String estado, String reporteManual) {
        ReportPlantDetailDto detail = new ReportPlantDetailDto();
        detail.setPlantGroupCode(label);
        detail.setFinalState(estado);
        detail.setSummary(normalizeText(reporteManual));
        ReportFindingDto finding = new ReportFindingDto();
        finding.setSide("REGISTRO");
        finding.setNote("Analisis manual asociado a la etiqueta seleccionada.");
        detail.setFindings(List.of(finding));
        return detail;
    }

    private PlantAnalysisHistoryItemDto toHistoryItem(PlantAnalysisRecord analysisRecord) {
        List<PlantAnalysisRecordImage> images = plantAnalysisRecordImageRepository.findByAnalysisRecordIdOrderBySortOrderAsc(analysisRecord.getId());
        return PlantAnalysisHistoryItemDto.builder()
                .id(analysisRecord.getId())
                .sourceType(normalizeSourceType(analysisRecord.getSourceType()))
                .estadoGeneral(analysisRecord.getEstadoGeneral())
                .urgencia(analysisRecord.getUrgencia())
                .confianza(analysisRecord.getConfianza() == null ? 0.0 : analysisRecord.getConfianza())
                .summaryText(analysisRecord.getSummaryText())
                .operatorNotes(analysisRecord.getOperatorNotes())
                .hallazgos(readJsonStringArray(analysisRecord.getHallazgosJson()))
                .recomendaciones(readJsonStringArray(analysisRecord.getRecomendacionesJson()))
                .modeloIa(analysisRecord.getModeloIa())
                .proveedorIa(analysisRecord.getProveedorIa())
                .requiereRevisionManual(analysisRecord.isRequiereRevisionManual())
                .fallback(analysisRecord.isFallback())
                .patrolId(analysisRecord.getPatrolId())
                .reportId(analysisRecord.getReportId())
                .reportTitle(analysisRecord.getReportTitleSnapshot())
                .generatedByName(analysisRecord.getGeneratedBy().getFullName())
                .generalLabels(readJsonStringArray(analysisRecord.getGeneralLabelsJson()))
                .exactLabels(readJsonStringArray(analysisRecord.getExactLabelsJson()))
                .images(images.stream().map(this::toHistoryImage).toList())
                .createdAt(analysisRecord.getCreatedAt())
                .build();
    }

    private PlantAnalysisHistoryImageDto toHistoryImage(PlantAnalysisRecordImage image) {
        return PlantAnalysisHistoryImageDto.builder()
                .id(image.getId())
                .imageUrl("/api/analisis/images/" + image.getId())
                .mimeType(image.getMimeType())
                .sortOrder(image.getSortOrder())
                .build();
    }

    private Map<String, Object> buildGeminiResponseSchema() {
        return Map.of(
                "type", "OBJECT",
                "properties", Map.of(
                        "estadoGeneral", Map.of("type", "STRING", "enum", ALLOWED_STATES),
                        "urgencia", Map.of("type", "STRING", "enum", ALLOWED_URGENCY),
                        "confianza", Map.of("type", "NUMBER"),
                        "diagnostico", Map.of("type", "STRING"),
                        "hallazgos", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "recomendaciones", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "requiereRevisionManual", Map.of("type", "BOOLEAN")
                ),
                "required", List.of(
                        "estadoGeneral",
                        "urgencia",
                        "confianza",
                        "diagnostico",
                        "hallazgos",
                        "recomendaciones",
                        "requiereRevisionManual"
                )
        );
    }

    private String extractGeminiText(JsonNode root) {
        JsonNode parts = root.path("candidates").path(0).path("content").path("parts");
        if (!parts.isArray()) {
            return null;
        }
        for (JsonNode part : parts) {
            JsonNode text = part.get("text");
            if (text != null && !text.isNull()) {
                return text.asText();
            }
        }
        return null;
    }

    private String normalizeChoice(String value, List<String> allowedValues, String fallbackValue) {
        if (value == null || value.isBlank()) {
            return fallbackValue;
        }
        String normalized = value.trim().toUpperCase(Locale.ROOT);
        return allowedValues.contains(normalized) ? normalized : fallbackValue;
    }

    private List<String> readStringArray(JsonNode node) {
        if (!node.isArray()) {
            return List.of();
        }
        List<String> values = new ArrayList<>();
        for (JsonNode item : node) {
            String value = item.asText("").trim();
            if (!value.isBlank()) {
                values.add(value);
            }
        }
        return values;
    }

    private List<String> readJsonStringArray(String rawJson) {
        if (rawJson == null || rawJson.isBlank()) {
            return List.of();
        }
        try {
            return Arrays.stream(objectMapper.readValue(rawJson, String[].class))
                    .map(value -> value == null ? "" : value.trim())
                    .filter(value -> !value.isBlank())
                    .toList();
        } catch (Exception ex) {
            return List.of();
        }
    }

    private String normalizeOperatorNotes(String notes) {
        if (notes == null || notes.isBlank()) {
            return "Sin observaciones del operador.";
        }
        return notes.trim();
    }

    private String normalizeText(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private List<String> normalizeLabels(List<String> labels) {
        if (labels == null || labels.isEmpty()) {
            return List.of();
        }
        Set<String> seen = new HashSet<>();
        List<String> normalized = new ArrayList<>();
        for (String label : labels) {
            if (label == null) {
                continue;
            }
            String value = label.trim().toUpperCase(Locale.ROOT);
            if (!value.isBlank() && seen.add(value)) {
                normalized.add(value);
            }
        }
        return normalized;
    }

    private String writeStringArray(List<String> values) {
        try {
            return objectMapper.writeValueAsString(values == null ? List.of() : values);
        } catch (Exception ex) {
            throw new BusinessException("Could not serialize analysis list data", "ANALYSIS_LIST_SERIALIZATION_ERROR");
        }
    }

    private String writeReportPlantDetails(List<ReportPlantDetailDto> details) {
        try {
            return objectMapper.writeValueAsString(details == null ? List.of() : details);
        } catch (Exception ex) {
            throw new BusinessException("Could not serialize manual report details", "MANUAL_REPORT_SERIALIZATION_ERROR");
        }
    }

    private String normalizeSourceType(String value) {
        if (value == null || value.isBlank()) {
            return "MANUAL";
        }
        String normalized = value.trim().toUpperCase(Locale.ROOT);
        return ALLOWED_SOURCE_TYPES.contains(normalized) ? normalized : "MANUAL";
    }

    private String normalizeAnalysisProvider(String provider) {
        if (provider == null || provider.isBlank()) {
            return "manual";
        }
        return provider.trim().toLowerCase(Locale.ROOT);
    }

    private String buildAnalysisNotes(PlantAnalysisRecord analysisRecord) {
        List<String> notes = new ArrayList<>();
        if (analysisRecord.isFallback()) {
            notes.add("El analisis se resolvio con fallback local.");
        }
        if (analysisRecord.getProveedorIa() != null && !analysisRecord.getProveedorIa().isBlank()) {
            notes.add("Proveedor IA: " + analysisRecord.getProveedorIa().trim());
        }
        if (analysisRecord.getModeloIa() != null && !analysisRecord.getModeloIa().isBlank()) {
            notes.add("Modelo IA: " + analysisRecord.getModeloIa().trim());
        }
        if (analysisRecord.isRequiereRevisionManual()) {
            notes.add("El resultado recomienda revision manual.");
        }
        return notes.isEmpty() ? null : String.join(" ", notes);
    }

    private String trimTrailingSlash(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }

    private double clamp(double value) {
        if (value < 0.0) {
            return 0.0;
        }
        if (value > 1.0) {
            return 1.0;
        }
        return value;
    }

    private User findUserOrThrow(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));
    }

    private static final class PlantAnalysisImageRequestDtoBuilder {
        private PlantAnalysisImageRequestDtoBuilder() {
        }

        private static PlantAnalysisImageRequestDto of(String imagenBase64, String mimeType) {
            PlantAnalysisImageRequestDto dto = new PlantAnalysisImageRequestDto();
            dto.setImagenBase64(imagenBase64);
            dto.setMimeType(mimeType);
            return dto;
        }
    }
}
