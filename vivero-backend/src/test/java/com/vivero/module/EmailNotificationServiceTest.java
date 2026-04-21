package com.vivero.module.reports;

import com.vivero.config.AppProperties;
import com.vivero.module.auth.entity.User;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.service.notification.EmailNotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import jakarta.mail.Session;
import jakarta.mail.internet.MimeMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mail.MailAuthenticationException;
import org.springframework.mail.javamail.JavaMailSender;

import java.time.LocalDateTime;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class EmailNotificationServiceTest {

    @Mock
    private JavaMailSender mailSender;

    private EmailNotificationService emailNotificationService;

    @BeforeEach
    void setUp() {
        AppProperties properties = new AppProperties();
        properties.getNotification().getEmail().setFrom("noreply@vivero.com");
        emailNotificationService = new EmailNotificationService(mailSender, properties);
    }

    @Test
    void sendReportNotificationShouldTranslateAuthFailure() {
        MimeMessage mimeMessage = new MimeMessage(Session.getDefaultInstance(new Properties()));
        when(mailSender.createMimeMessage()).thenReturn(mimeMessage);
        doThrow(new MailAuthenticationException("bad credentials")).when(mailSender).send(mimeMessage);

        BusinessException ex = assertThrows(
                BusinessException.class,
                () -> emailNotificationService.sendReportNotification(buildReport(), buildConfig(), new byte[]{1, 2, 3})
        );

        assertEquals("EMAIL_PROVIDER_AUTH_FAILED", ex.getCode());
    }

    private Report buildReport() {
        User user = User.builder()
                .firstName("System")
                .lastName("Admin")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        Report report = Report.builder()
                .patrolId(1001L)
                .generatedBy(user)
                .title("Seed report")
                .summary("Summary")
                .observationsCount(1)
                .healthyCount(1)
                .attentionCount(0)
                .dangerCount(0)
                .manualReviewCount(0)
                .inconclusiveCount(0)
                .pdfPath("/tmp/report.pdf")
                .build();
        report.setId(99L);
        report.setCreatedAt(LocalDateTime.now());
        return report;
    }

    private NotificationConfig buildConfig() {
        return NotificationConfig.builder()
                .channel(NotificationChannel.EMAIL)
                .contactValue("ana@vivero.com")
                .active(true)
                .build();
    }
}
