package com.vivero.module.reports;

import com.vivero.config.AppProperties;
import com.vivero.module.auth.entity.User;
import com.vivero.module.reports.dto.ReportFindingDto;
import com.vivero.module.reports.dto.ReportPlantDetailDto;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.pdf.PdfReportGenerator;
import com.vivero.module.reports.service.notification.EmailNotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.enums.UserRole;
import com.fasterxml.jackson.databind.ObjectMapper;
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
        String envelopeFrom = required("MANUAL_MAIL_SMTP_ENVELOPE_FROM", mailFrom);
        String smtpLocalhost = required("MANUAL_MAIL_SMTP_LOCALHOST", domainFrom(mailFrom));

        AppProperties properties = new AppProperties();
        properties.getStorage().setImagesPath("target/manual-mail-artifacts");
        properties.getNotification().getEmail().setFrom(mailFrom);

        PdfReportGenerator pdfReportGenerator = new PdfReportGenerator(properties, new ObjectMapper());
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
        javaMailProps.put("mail.smtp.from", envelopeFrom);
        javaMailProps.put("mail.smtp.localhost", smtpLocalhost);
        javaMailProps.put("mail.smtp.connectiontimeout", "10000");
        javaMailProps.put("mail.smtp.timeout", "15000");
        javaMailProps.put("mail.smtp.writetimeout", "15000");

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
                .manualReviewCount(0)
                .inconclusiveCount(0)
                .plantDetailsJson(buildPlantDetailsJson())
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

    private String buildPlantDetailsJson() {
        try {
            ReportFindingDto finding = new ReportFindingDto();
            finding.setSide("DR");
            finding.setNote("Se observaron hojas con manchas leves y evidencia lateral.");

            ReportPlantDetailDto detail = new ReportPlantDetailDto();
            detail.setPlantGroupCode("PLA_1_M_15");
            detail.setFinalState("ATENCION");
            detail.setSummary("La planta presenta signos leves que requieren seguimiento.");
            detail.setFindings(java.util.List.of(finding));

            return new ObjectMapper().writeValueAsString(java.util.List.of(detail));
        } catch (Exception ex) {
            throw new IllegalStateException("Could not build manual mail report details", ex);
        }
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

    private String domainFrom(String email) {
        int atIndex = email == null ? -1 : email.indexOf('@');
        if (atIndex < 0 || atIndex == email.length() - 1) {
            return "localhost";
        }
        return email.substring(atIndex + 1);
    }
}
