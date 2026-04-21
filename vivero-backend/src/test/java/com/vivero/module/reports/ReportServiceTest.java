package com.vivero.module.reports;

import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.reports.dto.GenerateReportRequestDto;
import com.vivero.module.reports.dto.NotificationChannelConfigRequestDto;
import com.vivero.module.reports.dto.NotificationConfigDto;
import com.vivero.module.reports.dto.NotifyReportRequestDto;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.mapper.ReportMapper;
import com.vivero.module.reports.pdf.PdfReportGenerator;
import com.vivero.module.reports.repository.NotificationConfigRepository;
import com.vivero.module.reports.repository.ReportRepository;
import com.vivero.module.reports.service.impl.ReportServiceImpl;
import com.vivero.module.reports.service.notification.NotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ReportServiceTest {

    @Mock
    private ReportRepository reportRepository;

    @Mock
    private NotificationConfigRepository notificationConfigRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private PdfReportGenerator pdfReportGenerator;

    @Mock
    private NotificationService emailNotificationService;

    private ReportServiceImpl reportService;

    private User user;

    @BeforeEach
    void setUp() {
        reportService = new ReportServiceImpl(
                reportRepository,
                notificationConfigRepository,
                userRepository,
                new ReportMapper(new com.fasterxml.jackson.databind.ObjectMapper()),
                pdfReportGenerator,
                List.of(emailNotificationService),
                new com.fasterxml.jackson.databind.ObjectMapper()
        );

        user = User.builder()
                .firstName("Edgar")
                .lastName("Castillo")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();
        user.setId(1L);
    }

    @Test
    void generateReportShouldPersistAndReturnDto() {
        GenerateReportRequestDto request = new GenerateReportRequestDto();
        request.setPatrolId(10L);
        request.setTitle("Patrol 10 summary");
        request.setSummary("Observed mixed plant states");
        request.setObservationsCount(3);
        request.setHealthyCount(1);
        request.setAttentionCount(1);
        request.setDangerCount(1);
        request.setManualReviewCount(0);
        request.setInconclusiveCount(0);

        when(userRepository.findByEmail("admin@vivero.com")).thenReturn(Optional.of(user));
        when(reportRepository.save(any(Report.class))).thenAnswer(invocation -> {
            Report report = invocation.getArgument(0);
            if (report.getId() == null) {
                report.setId(99L);
            }
            report.setCreatedAt(LocalDateTime.now());
            return report;
        });
        when(pdfReportGenerator.generateAndStore(any(Report.class))).thenReturn("/app/images/reports/report-99.pdf");

        var response = reportService.generateReport(request, "admin@vivero.com");

        assertEquals(99L, response.getId());
        assertEquals(10L, response.getPatrolId());
        assertEquals("/app/images/reports/report-99.pdf", response.getPdfPath());

        ArgumentCaptor<Report> captor = ArgumentCaptor.forClass(Report.class);
        verify(reportRepository).save(captor.capture());
        assertEquals("Patrol 10 summary", captor.getValue().getTitle());
    }

    @Test
    void saveNotificationConfigsShouldUpsertChannels() {
        NotificationConfigDto configDto = NotificationConfigDto.builder()
                .channel(NotificationChannel.EMAIL)
                .contactValue("admin@vivero.com")
                .active(true)
                .build();

        when(userRepository.findByEmail("admin@vivero.com")).thenReturn(Optional.of(user));
        when(notificationConfigRepository.findByUserIdAndChannel(1L, NotificationChannel.EMAIL))
                .thenReturn(Optional.empty());
        when(notificationConfigRepository.save(any(NotificationConfig.class))).thenAnswer(invocation -> {
            NotificationConfig config = invocation.getArgument(0);
            config.setId(50L);
            return config;
        });

        var response = reportService.saveNotificationConfigs(List.of(configDto), "admin@vivero.com");

        assertEquals(1, response.size());
        assertEquals(NotificationChannel.EMAIL, response.get(0).getChannel());
        verify(notificationConfigRepository).save(any(NotificationConfig.class));
    }

    @Test
    void saveNotificationConfigShouldRejectInvalidEmail() {
        NotificationChannelConfigRequestDto request = new NotificationChannelConfigRequestDto();
        request.setContactValue("correo-invalido");
        request.setActive(true);

        when(userRepository.findByEmail("admin@vivero.com")).thenReturn(Optional.of(user));

        assertThrows(
                BusinessException.class,
                () -> reportService.saveNotificationConfig(NotificationChannel.EMAIL, request, "admin@vivero.com")
        );
    }

    @Test
    void toggleNotificationChannelShouldUpdateExistingConfig() {
        NotificationConfig config = NotificationConfig.builder()
                .user(user)
                .channel(NotificationChannel.EMAIL)
                .contactValue("admin@vivero.com")
                .active(true)
                .build();
        config.setId(7L);

        when(userRepository.findByEmail("admin@vivero.com")).thenReturn(Optional.of(user));
        when(notificationConfigRepository.findByUserIdAndChannel(1L, NotificationChannel.EMAIL))
                .thenReturn(Optional.of(config));
        when(notificationConfigRepository.save(any(NotificationConfig.class))).thenAnswer(invocation -> invocation.getArgument(0));

        var response = reportService.toggleNotificationChannel(NotificationChannel.EMAIL, false, "admin@vivero.com");

        assertEquals(NotificationChannel.EMAIL, response.getChannel());
        assertEquals(false, response.getActive());
    }

    @Test
    void notifyReportShouldFailWhenNoActiveConfigs() {
        NotifyReportRequestDto request = new NotifyReportRequestDto();
        request.setReportId(10L);

        Report report = Report.builder()
                .patrolId(10L)
                .generatedBy(user)
                .title("Report")
                .observationsCount(1)
                .healthyCount(1)
                .attentionCount(0)
                .dangerCount(0)
                .manualReviewCount(0)
                .inconclusiveCount(0)
                .pdfPath("/tmp/report.pdf")
                .build();
        report.setId(10L);
        report.setCreatedAt(LocalDateTime.now());

        when(userRepository.findByEmail("admin@vivero.com")).thenReturn(Optional.of(user));
        when(reportRepository.findById(10L)).thenReturn(Optional.of(report));
        when(notificationConfigRepository.findByUserIdAndActiveTrue(1L)).thenReturn(List.of());

        assertThrows(BusinessException.class, () -> reportService.notifyReport(request, "admin@vivero.com"));
        verify(emailNotificationService, times(0)).sendReportNotification(any(), any(), any());
    }
}
