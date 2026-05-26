package com.vivero.module.reports;

import com.fasterxml.jackson.databind.ObjectMapper;
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
import org.junit.jupiter.api.Test;
import org.springframework.mail.javamail.JavaMailSenderImpl;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

class SmtpDiagnosticsManualTest {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Test
    void shouldRunDiagnosticsAcrossSupportedGoogleSmtpVariants() throws Exception {
        assumeTrue(Boolean.getBoolean("manual.smtp.diagnostics"), "Manual SMTP diagnostics disabled");

        String mailTo = required("MANUAL_MAIL_TO", "ferchocastfun15@gmail.com");
        String runtimeFrom = required("MAIL_FROM", "noreply@vivero.com");
        String runtimeUsername = optional("MAIL_USERNAME");
        String runtimePassword = optional("MAIL_PASSWORD");
        Path artifactDir = Path.of("target", "manual-mail-artifacts");
        Files.createDirectories(artifactDir);

        AppProperties properties = new AppProperties();
        properties.getStorage().setImagesPath(artifactDir.toString());
        properties.getNotification().getEmail().setFrom(runtimeFrom);

        PdfReportGenerator pdfReportGenerator = new PdfReportGenerator(properties, OBJECT_MAPPER);
        Report report = buildReport(runtimeFrom);
        report.setPdfPath(pdfReportGenerator.generateAndStore(report));
        byte[] pdfContent = Files.readAllBytes(Path.of(report.getPdfPath()));

        List<ScenarioResult> results = new ArrayList<>();
        results.add(runScenario(
                "runtime-gmail-starttls-587",
                runtimeFrom,
                mailTo,
                "smtp.gmail.com",
                587,
                runtimeUsername,
                runtimePassword,
                false,
                true,
                true,
                report,
                pdfContent
        ));
        results.add(runScenario(
                "gmail-ssl-465",
                runtimeFrom,
                mailTo,
                "smtp.gmail.com",
                465,
                runtimeUsername,
                runtimePassword,
                true,
                false,
                true,
                report,
                pdfContent
        ));
        results.add(runScenario(
                "google-relay-starttls-587-no-auth",
                required("MANUAL_MAIL_FROM", "reportes@agrotechnologyrobotics.com"),
                mailTo,
                required("MANUAL_MAIL_HOST", "smtp-relay.gmail.com"),
                Integer.parseInt(required("MANUAL_MAIL_PORT", "587")),
                "",
                "",
                false,
                true,
                false,
                report,
                pdfContent
        ));

        Path reportPath = artifactDir.resolve("smtp-diagnostics-report.md");
        Files.writeString(reportPath, renderMarkdownReport(report, results), StandardCharsets.UTF_8);

        assertTrue(Files.exists(reportPath), "SMTP diagnostics report must be generated");
        assertTrue(pdfContent.length > 0, "Generated PDF must not be empty");
    }

    private ScenarioResult runScenario(
            String name,
            String from,
            String to,
            String host,
            int port,
            String username,
            String password,
            boolean ssl,
            boolean startTls,
            boolean auth,
            Report report,
            byte[] pdfContent
    ) {
        ScenarioResult result = new ScenarioResult();
        result.name = name;
        result.from = from;
        result.to = to;
        result.host = host;
        result.port = port;
        result.auth = auth;
        result.startTls = startTls;
        result.ssl = ssl;
        result.usernameConfigured = username != null && !username.isBlank();
        result.passwordConfigured = password != null && !password.isBlank();

        AppProperties properties = new AppProperties();
        properties.getNotification().getEmail().setFrom(from);

        try {
            JavaMailSenderImpl mailSender = new JavaMailSenderImpl();
            mailSender.setHost(host);
            mailSender.setPort(port);
            mailSender.setProtocol("smtp");
            if (result.usernameConfigured) {
                mailSender.setUsername(username);
            }
            if (result.passwordConfigured) {
                mailSender.setPassword(password);
            }

            Properties javaMailProps = mailSender.getJavaMailProperties();
            javaMailProps.put("mail.smtp.auth", Boolean.toString(auth));
            javaMailProps.put("mail.smtp.starttls.enable", Boolean.toString(startTls));
            javaMailProps.put("mail.smtp.starttls.required", Boolean.toString(startTls));
            javaMailProps.put("mail.smtp.ssl.enable", Boolean.toString(ssl));
            javaMailProps.put("mail.smtp.connectiontimeout", "10000");
            javaMailProps.put("mail.smtp.timeout", "15000");
            javaMailProps.put("mail.smtp.writetimeout", "15000");

            EmailNotificationService service = new EmailNotificationService(mailSender, properties);
            service.sendReportNotification(report, buildConfig(to), pdfContent);

            result.outcome = "SUCCESS";
        } catch (Exception ex) {
            result.outcome = "FAILURE";
            result.exceptionClass = ex.getClass().getName();
            result.message = ex.getMessage();
            Throwable rootCause = rootCause(ex);
            if (rootCause != null && rootCause != ex) {
                result.rootCauseClass = rootCause.getClass().getName();
                result.rootCauseMessage = rootCause.getMessage();
            }
            result.stackTrace = stackTrace(ex);
        }

        return result;
    }

    private String renderMarkdownReport(Report report, List<ScenarioResult> results) {
        StringBuilder builder = new StringBuilder();
        builder.append("# SMTP diagnostics report\n\n");
        builder.append("Generated at: ").append(LocalDateTime.now()).append("\n");
        builder.append("Report title: ").append(report.getTitle()).append("\n");
        builder.append("Proof PDF: ").append(report.getPdfPath()).append("\n");
        builder.append("Target recipient: ").append(required("MANUAL_MAIL_TO", "ferchocastfun15@gmail.com")).append("\n\n");
        builder.append("| Scenario | Host | Port | Auth | STARTTLS | SSL | User set | Password set | Outcome |\n");
        builder.append("| --- | --- | ---: | --- | --- | --- | --- | --- | --- |\n");
        for (ScenarioResult result : results) {
            builder.append("| ")
                    .append(result.name).append(" | ")
                    .append(result.host).append(" | ")
                    .append(result.port).append(" | ")
                    .append(result.auth).append(" | ")
                    .append(result.startTls).append(" | ")
                    .append(result.ssl).append(" | ")
                    .append(result.usernameConfigured).append(" | ")
                    .append(result.passwordConfigured).append(" | ")
                    .append(result.outcome).append(" |\n");
        }

        builder.append("\n## Details\n\n");
        for (ScenarioResult result : results) {
            builder.append("### ").append(result.name).append("\n");
            builder.append("- From: ").append(result.from).append("\n");
            builder.append("- To: ").append(result.to).append("\n");
            builder.append("- Host: ").append(result.host).append("\n");
            builder.append("- Port: ").append(result.port).append("\n");
            builder.append("- Outcome: ").append(result.outcome).append("\n");
            if (result.exceptionClass != null) {
                builder.append("- Exception: ").append(result.exceptionClass).append("\n");
            }
            if (result.message != null) {
                builder.append("- Message: ").append(result.message.replace("\r", " ").replace("\n", " ")).append("\n");
            }
            if (result.rootCauseClass != null) {
                builder.append("- Root cause: ").append(result.rootCauseClass).append("\n");
            }
            if (result.rootCauseMessage != null) {
                builder.append("- Root cause message: ")
                        .append(result.rootCauseMessage.replace("\r", " ").replace("\n", " "))
                        .append("\n");
            }
            if (result.stackTrace != null) {
                builder.append("\n```text\n").append(result.stackTrace).append("\n```\n");
            }
            builder.append("\n");
        }
        return builder.toString();
    }

    private Report buildReport(String from) throws Exception {
        User user = User.builder()
                .firstName("Sistema")
                .lastName("SMTP")
                .email(from)
                .password("not-used")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        ReportFindingDto finding = new ReportFindingDto();
        finding.setSide("IZ");
        finding.setNote("Prueba de diagnostico SMTP con PDF adjunto.");

        ReportPlantDetailDto detail = new ReportPlantDetailDto();
        detail.setPlantGroupCode("PLA_1_MA_1_IZ");
        detail.setFinalState("ATENCION");
        detail.setSummary("Generacion de evidencia para validar envio por correo.");
        detail.setFindings(List.of(finding));

        Report report = Report.builder()
                .patrolId(20260520L)
                .generatedBy(user)
                .title("Diagnostico SMTP Google")
                .summary("Prueba automatizada de variantes SMTP sobre Gmail y relay.")
                .observationsCount(1)
                .healthyCount(0)
                .attentionCount(1)
                .dangerCount(0)
                .manualReviewCount(0)
                .inconclusiveCount(0)
                .plantDetailsJson(OBJECT_MAPPER.writeValueAsString(List.of(detail)))
                .build();

        report.setId(20260520L);
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

    private String optional(String key) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) {
            value = System.getProperty(key);
        }
        return value == null ? "" : value;
    }

    private String required(String key, String fallback) {
        String value = optional(key);
        return value.isBlank() ? fallback : value;
    }

    private String stackTrace(Exception ex) {
        StringWriter writer = new StringWriter();
        ex.printStackTrace(new PrintWriter(writer));
        return writer.toString();
    }

    private Throwable rootCause(Throwable throwable) {
        Throwable current = throwable;
        while (current.getCause() != null && current.getCause() != current) {
            current = current.getCause();
        }
        return current;
    }

    private static class ScenarioResult {
        private String name;
        private String from;
        private String to;
        private String host;
        private int port;
        private boolean auth;
        private boolean startTls;
        private boolean ssl;
        private boolean usernameConfigured;
        private boolean passwordConfigured;
        private String outcome;
        private String exceptionClass;
        private String message;
        private String rootCauseClass;
        private String rootCauseMessage;
        private String stackTrace;
    }
}
