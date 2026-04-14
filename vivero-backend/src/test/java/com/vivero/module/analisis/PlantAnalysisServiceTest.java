package com.vivero.module.analisis;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vivero.module.analisis.dto.PlantAnalysisRequest;
import com.vivero.module.analisis.dto.PlantAnalysisResponse;
import com.vivero.module.analisis.entity.PlantReport;
import com.vivero.module.analisis.repository.PlantReportRepository;
import com.vivero.module.analisis.service.impl.PlantAnalysisServiceImpl;
import com.vivero.module.analisis.service.vision.VisionApiClient;
import com.vivero.module.analisis.service.vision.VisionDiagnosis;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PlantAnalysisServiceTest {

    @Mock
    private PlantReportRepository plantReportRepository;

    @Mock
    private VisionApiClient visionApiClient;

    @Mock
    private SimpMessagingTemplate messagingTemplate;

    @InjectMocks
    private PlantAnalysisServiceImpl plantAnalysisService;

    @BeforeEach
    void setUp() {
        plantAnalysisService = new PlantAnalysisServiceImpl(
                plantReportRepository,
                visionApiClient,
                messagingTemplate,
                new ObjectMapper()
        );
    }

    @Test
    void shouldPersistAnalysisAndBroadcastTopics() {
        PlantAnalysisRequest request = new PlantAnalysisRequest();
        request.setImagenBase64("ZmFrZS1pbWFnZQ==");
        request.setMimeType("image/jpeg");
        request.setObservacionesOperador("Hojas con manchas amarillas");

        VisionDiagnosis diagnosis = VisionDiagnosis.builder()
                .estadoGeneral("ATTENTION")
                .confianza(new BigDecimal("0.812"))
                .hallazgos(List.of("Manchas foliares", "Coloracion irregular"))
                .diagnostico("Se observan signos tempranos de estres.")
                .recomendaciones(List.of("Revisar riego", "Inspeccionar plaga"))
                .urgencia("CRITICA")
                .modeloIa("gemini-1.5-flash")
                .build();

        PlantReport savedReport = PlantReport.builder()
                .id(UUID.fromString("11111111-1111-1111-1111-111111111111"))
                .imagenUrl("memory://analisis/inline-upload.jpg")
                .observacionesOperador("Hojas con manchas amarillas")
                .estadoGeneral("ATTENTION")
                .confianza(new BigDecimal("0.812"))
                .hallazgos("[\"Manchas foliares\",\"Coloracion irregular\"]")
                .diagnostico("Se observan signos tempranos de estres.")
                .recomendaciones("[\"Revisar riego\",\"Inspeccionar plaga\"]")
                .urgencia("CRITICA")
                .modeloIa("gemini-1.5-flash")
                .createdAt(OffsetDateTime.parse("2026-04-14T10:15:30Z"))
                .build();

        when(visionApiClient.analyzePlantImage(any(), any(), any())).thenReturn(diagnosis);
        when(plantReportRepository.save(any(PlantReport.class))).thenReturn(savedReport);

        PlantAnalysisResponse response = plantAnalysisService.analyzePlant(request);

        assertThat(response.getId()).isEqualTo(savedReport.getId());
        assertThat(response.getUrgencia()).isEqualTo("CRITICA");
        assertThat(response.getHallazgos()).containsExactly("Manchas foliares", "Coloracion irregular");

        ArgumentCaptor<PlantReport> captor = ArgumentCaptor.forClass(PlantReport.class);
        verify(plantReportRepository).save(captor.capture());
        assertThat(captor.getValue().getObservacionesOperador()).isEqualTo("Hojas con manchas amarillas");

        verify(messagingTemplate).convertAndSend(eq("/topic/analisis"), any(PlantAnalysisResponse.class));
        verify(messagingTemplate).convertAndSend(eq("/topic/alertas"), any(PlantAnalysisResponse.class));
    }
}
