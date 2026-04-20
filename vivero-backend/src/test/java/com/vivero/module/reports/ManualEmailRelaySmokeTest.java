package com.vivero.module.reports;

import com.vivero.config.AppProperties;
import com.vivero.module.auth.entity.User;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.pdf.PdfReportGenerator;
import com.vivero.module.reports.service.notification.EmailNotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.enums.UserRole;
import org.junit.jupiter.api.Test;
import org.springframework.mail.javamail.JavaMailSenderImpl;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

class ManualEmailRelaySmokeTest {

    @Test
    void shouldGeneratePdfAndSendRealEmailThroughGoogleRelay() throws Exception {
        assumeTrue(Boolean.getBoolean("manual.mail.test"), "Manual mail smoke test disabled");

        String mailFrom = required("MANUAL_MAIL_FROM", "reportes@agrotechnologyrobotics.com");
        String mailTo = required("MANUAL_MAIL_TO", "ferchocastfun15@gmail.com");
        String mailHost = required("MANUAL_MAIL_HOST", "smtp-relay.gmail.com");
        int mailPort = Integer.parseInt(required("MANUAL_MAIL_PORT", "587"));

        AppProperties properties = new AppProperties();
        properties.getStorage().setImagesPath("target/manual-mail-artifacts");
        properties.getNotification().getEmail().setFrom(mailFrom);

        PdfReportGenerator pdfReportGenerator = new PdfReportGenerator(properties);
        Report report = buildReport();
        report.setPdfPath(pdfReportGenerator.generateAndStore(report));

        byte[] pdfContent = Files.readAllBytes(Path.of(report.getPdfPath()));
        assertTrue(pdfContent.length > 0, "Generated PDF must not be empty");

        JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
        mailSender.setHost(mailHost);
        mailSender.setPort(mailPort);
        mailSender.setProtocol("smtp");

        Properties javaMailProps = mailSender.getJavaMailProperties();
        javaMailProps.put("mail.smtp.auth", "false");
        javaMailProps.put("mail.smtp.starttls.enable", "true");
        javaMailProps.put("mail.smtp.starttls.required", "true");

        EmailNotificationService emailNotificationService = new EmailNotificationService(mailSender, properties);
        emailNotificationService.sendReportNotification(report, buildConfig(mailTo), pdfContent);
    }

    private Report buildReport() {
        User user = User.builder()
                .firstName("Sistema")
                .lastName("Vivero")
                .email(required("MANUAL_MAIL_FROM", "reportes@agrotechnologyrobotics.com"))
                .password("not-used")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        Report report = Report.builder()
                .patrolId(20260420L)
                .generatedBy(user)
                .title("Reporte real de prueba SMTP Relay")
                .summary("Prueba real de generacion PDF y envio por Google Workspace SMTP Relay.")
                .observationsCount(6)
                .healthyCount(3)
                .attentionCount(2)
                .dangerCount(1)
                .build();

        report.setId(20260420L);
        report.setCreatedAt(LocalDateTime.now());
        report.setUpdatedAt(LocalDateTime.now());
        return report;
    }

    private NotificationConfig buildConfig(String mailTo) {
        return NotificationConfig.builder()
                .channel(NotificationChannel.EMAIL)
                .contactValue(mailTo)
                .active(true)
                .build();
    }

    private String required(String key, String fallback) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) {
            value = System.getProperty(key);
        }
        if (value == null || value.isBlank()) {
            value = fallback;
        }
        return value;
    }
}
