package com.vivero.module.analisis.service.vision;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vivero.config.AppProperties;
import com.vivero.shared.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class ExternalVisionApiClient implements VisionApiClient {

    private final AppProperties appProperties;
    private final ObjectMapper objectMapper;

    @Override
    public VisionDiagnosis analyzePlantImage(String imageBase64, String mimeType, String operatorNotes) {
        AppProperties.VisionApi visionApi = appProperties.getVisionApi();
        String provider = normalizeProvider(visionApi.getProvider());

        return switch (provider) {
            case "gemini" -> analyzeWithGemini(imageBase64, mimeType, normalizeNotes(operatorNotes), visionApi);
            case "openai" -> analyzeWithOpenAi(imageBase64, mimeType, normalizeNotes(operatorNotes), visionApi);
            default -> throw new BusinessException(
                    "Unsupported vision provider: " + visionApi.getProvider(),
                    "VISION_PROVIDER_NOT_SUPPORTED"
            );
        };
    }

    private VisionDiagnosis analyzeWithGemini(
            String imageBase64,
            String mimeType,
            String operatorNotes,
            AppProperties.VisionApi visionApi
    ) {
        AppProperties.VisionApi.Provider provider = visionApi.getGemini();
        validateProviderConfig(provider.getKey(), provider.getUrl(), "gemini");

        try {
            Map<String, Object> payload = Map.of(
                    "contents", List.of(Map.of(
                            "role", "user",
                            "parts", List.of(
                                    Map.of("text", buildPrompt(operatorNotes)),
                                    Map.of("inline_data", Map.of(
                                            "mime_type", mimeType,
                                            "data", imageBase64
                                    ))
                            )
                    )),
                    "generationConfig", Map.of("responseMimeType", "application/json")
            );

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(provider.getUrl() + "?key=" + provider.getKey()))
                    .timeout(Duration.ofSeconds(visionApi.getTimeoutSeconds()))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(payload), StandardCharsets.UTF_8))
                    .build();

            JsonNode response = execute(request);
            String content = response.path("candidates").path(0).path("content").path("parts").path(0).path("text").asText();
            return parseDiagnosis(content, defaultModel(provider.getModel(), "gemini-1.5-flash"));
        } catch (BusinessException ex) {
            throw ex;
        } catch (Exception ex) {
            log.error("Error calling Gemini vision API", ex);
            throw new BusinessException("Failed to analyze image with Gemini", "VISION_PROVIDER_ERROR");
        }
    }

    private VisionDiagnosis analyzeWithOpenAi(
            String imageBase64,
            String mimeType,
            String operatorNotes,
            AppProperties.VisionApi visionApi
    ) {
        AppProperties.VisionApi.Provider provider = visionApi.getOpenai();
        validateProviderConfig(provider.getKey(), provider.getUrl(), "openai");

        try {
            Map<String, Object> payload = Map.of(
                    "model", defaultModel(provider.getModel(), "gpt-4o-mini"),
                    "response_format", Map.of("type", "json_object"),
                    "messages", List.of(
                            Map.of(
                                    "role", "system",
                                    "content", "You analyze pepper plant images and return only JSON."
                            ),
                            Map.of(
                                    "role", "user",
                                    "content", List.of(
                                            Map.of("type", "text", "text", buildPrompt(operatorNotes)),
                                            Map.of(
                                                    "type", "image_url",
                                                    "image_url", Map.of("url", "data:" + mimeType + ";base64," + imageBase64)
                                            )
                                    )
                            )
                    )
            );

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(provider.getUrl()))
                    .timeout(Duration.ofSeconds(visionApi.getTimeoutSeconds()))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + provider.getKey())
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(payload), StandardCharsets.UTF_8))
                    .build();

            JsonNode response = execute(request);
            String content = response.path("choices").path(0).path("message").path("content").asText();
            return parseDiagnosis(content, defaultModel(provider.getModel(), "gpt-4o-mini"));
        } catch (BusinessException ex) {
            throw ex;
        } catch (Exception ex) {
            log.error("Error calling OpenAI vision API", ex);
            throw new BusinessException("Failed to analyze image with OpenAI", "VISION_PROVIDER_ERROR");
        }
    }

    private JsonNode execute(HttpRequest request) throws Exception {
        HttpClient client = HttpClient.newBuilder().build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

        if (response.statusCode() >= 400) {
            throw new BusinessException(
                    "Vision provider rejected the request",
                    "VISION_PROVIDER_HTTP_" + response.statusCode()
            );
        }

        return objectMapper.readTree(response.body());
    }

    VisionDiagnosis parseDiagnosis(String rawJson, String modelName) throws Exception {
        JsonNode diagnosis = objectMapper.readTree(stripMarkdownFence(rawJson));

        String estadoGeneral = uppercaseOrDefault(diagnosis.path("estadoGeneral").asText(null), "UNKNOWN");
        BigDecimal confianza = parseConfidence(diagnosis.path("confianza"));
        List<String> hallazgos = readStringList(diagnosis.path("hallazgos"));
        String diagnostico = defaultText(diagnosis.path("diagnostico").asText(null), "Sin diagnostico disponible");
        List<String> recomendaciones = readStringList(diagnosis.path("recomendaciones"));
        String urgencia = uppercaseOrDefault(diagnosis.path("urgencia").asText(null), "MEDIA");

        if (hallazgos.isEmpty()) {
            hallazgos = List.of("Sin hallazgos estructurados reportados por el modelo");
        }
        if (recomendaciones.isEmpty()) {
            recomendaciones = List.of("Solicitar revision manual del operador");
        }

        return VisionDiagnosis.builder()
                .estadoGeneral(estadoGeneral)
                .confianza(confianza)
                .hallazgos(hallazgos)
                .diagnostico(diagnostico)
                .recomendaciones(recomendaciones)
                .urgencia(urgencia)
                .modeloIa(defaultModel(modelName, normalizeProvider(appProperties.getVisionApi().getProvider())))
                .build();
    }

    private String buildPrompt(String operatorNotes) {
        return """
                Analiza la imagen de una planta de chile pimiento y responde SOLO JSON con esta forma:
                {
                  "estadoGeneral": "HEALTHY|ATTENTION|DANGER|UNKNOWN",
                  "confianza": 0.0,
                  "hallazgos": ["texto"],
                  "diagnostico": "texto narrativo",
                  "recomendaciones": ["texto"],
                  "urgencia": "BAJA|MEDIA|ALTA|CRITICA"
                }
                Usa las observaciones del operador como contexto adicional: %s
                """.formatted(operatorNotes);
    }

    private void validateProviderConfig(String apiKey, String url, String provider) {
        if (apiKey == null || apiKey.isBlank() || url == null || url.isBlank()) {
            throw new BusinessException(
                    "Vision provider configuration is incomplete for " + provider,
                    "VISION_API_NOT_CONFIGURED"
            );
        }
    }

    private BigDecimal parseConfidence(JsonNode node) {
        if (node == null || node.isMissingNode() || node.isNull()) {
            return BigDecimal.valueOf(0.500).setScale(3, RoundingMode.HALF_UP);
        }
        BigDecimal confidence = node.decimalValue();
        if (confidence.compareTo(BigDecimal.ZERO) < 0) {
            return BigDecimal.ZERO.setScale(3, RoundingMode.HALF_UP);
        }
        if (confidence.compareTo(BigDecimal.ONE) > 0) {
            return BigDecimal.ONE.setScale(3, RoundingMode.HALF_UP);
        }
        return confidence.setScale(3, RoundingMode.HALF_UP);
    }

    private List<String> readStringList(JsonNode node) {
        List<String> values = new ArrayList<>();
        if (node == null || node.isMissingNode() || node.isNull()) {
            return values;
        }
        if (node.isArray()) {
            node.forEach(item -> {
                String value = defaultText(item.asText(null), null);
                if (value != null) {
                    values.add(value);
                }
            });
            return values;
        }
        if (node.isTextual()) {
            values.add(node.asText());
        }
        return values;
    }

    private String stripMarkdownFence(String value) {
        if (value == null) {
            return "{}";
        }
        String sanitized = value.trim();
        if (sanitized.startsWith("```")) {
            sanitized = sanitized.replaceFirst("^```json", "");
            sanitized = sanitized.replaceFirst("^```", "");
            sanitized = sanitized.replaceFirst("```$", "");
        }
        return sanitized.trim();
    }

    private String normalizeProvider(String provider) {
        return provider == null ? "gemini" : provider.trim().toLowerCase(Locale.ROOT);
    }

    private String normalizeNotes(String operatorNotes) {
        return defaultText(operatorNotes, "Sin observaciones adicionales del operador.");
    }

    private String uppercaseOrDefault(String value, String fallback) {
        return defaultText(value, fallback).toUpperCase(Locale.ROOT);
    }

    private String defaultModel(String model, String fallback) {
        return defaultText(model, fallback);
    }

    private String defaultText(String value, String fallback) {
        if (value == null || value.trim().isEmpty()) {
            return fallback;
        }
        return value.trim();
    }
}
