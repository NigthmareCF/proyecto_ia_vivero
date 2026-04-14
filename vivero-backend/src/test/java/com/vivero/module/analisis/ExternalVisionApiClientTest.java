package com.vivero.module.analisis;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vivero.config.AppProperties;
import com.vivero.module.analisis.service.vision.ExternalVisionApiClient;
import com.vivero.module.analisis.service.vision.VisionDiagnosis;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class ExternalVisionApiClientTest {

    @Test
    void shouldParseStructuredDiagnosisPayload() throws Exception {
        AppProperties properties = new AppProperties();
        ExternalVisionApiClient client = new ExternalVisionApiClient(properties, new ObjectMapper());

        VisionDiagnosis diagnosis = client.parseDiagnosis("""
                {
                  "estadoGeneral": "danger",
                  "confianza": 0.9321,
                  "hallazgos": ["Necrosis en bordes", "Marchitez localizada"],
                  "diagnostico": "Hay dano avanzado por estres hidrico.",
                  "recomendaciones": ["Aplicar riego controlado", "Aislar la planta"],
                  "urgencia": "critica"
                }
                """, "gpt-4o-mini");

        assertThat(diagnosis.getEstadoGeneral()).isEqualTo("DANGER");
        assertThat(diagnosis.getUrgencia()).isEqualTo("CRITICA");
        assertThat(diagnosis.getRecomendaciones()).containsExactly("Aplicar riego controlado", "Aislar la planta");
        assertThat(diagnosis.getConfianza().toPlainString()).isEqualTo("0.932");
    }
}
