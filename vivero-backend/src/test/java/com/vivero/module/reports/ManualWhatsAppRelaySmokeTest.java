package com.vivero.module.reports;

import com.vivero.config.AppProperties;
import com.vivero.module.auth.entity.User;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.service.notification.WhatsAppNotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.enums.UserRole;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assumptions.assumeTrue;

class ManualWhatsAppRelaySmokeTest {

    @Test
    void shouldSendRealWhatsappThroughTwilio() {
        assumeTrue(Boolean.getBoolean("manual.whatsapp.test"), "Manual WhatsApp smoke test disabled");

        String accountSid = required("TWILIO_ACCOUNT_SID");
        String authToken = required("TWILIO_AUTH_TOKEN");
        String whatsappFrom = required("TWILIO_WHATSAPP_FROM");
        String whatsappTo = required("MANUAL_WHATSAPP_TO");

        AppProperties properties = new AppProperties();
        properties.getNotification().getTwilio().setAccountSid(accountSid);
        properties.getNotification().getTwilio().setAuthToken(authToken);
        properties.getNotification().getTwilio().setFromWhatsapp(whatsappFrom);

        WhatsAppNotificationService whatsAppNotificationService = new WhatsAppNotificationService(properties);
        whatsAppNotificationService.sendReportNotification(buildReport(), buildConfig(whatsappTo), new byte[0]);
    }

    private Report buildReport() {
        User user = User.builder()
                .firstName("Sistema")
                .lastName("Vivero")
                .email("reportes@agrotechnologyrobotics.com")
                .password("not-used")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        Report report = Report.builder()
                .patrolId(20260420L)
                .generatedBy(user)
                .title("Prueba WhatsApp backend")
                .summary("Mensaje de prueba enviado desde el modulo reports del backend por WhatsApp.")
                .observationsCount(4)
                .healthyCount(2)
                .attentionCount(1)
                .dangerCount(1)
                .pdfPath("/app/images/reports/report-20260420.pdf")
                .build();

        report.setId(20260420L);
        report.setCreatedAt(LocalDateTime.now());
        report.setUpdatedAt(LocalDateTime.now());
        return report;
    }

    private NotificationConfig buildConfig(String whatsappTo) {
        return NotificationConfig.builder()
                .channel(NotificationChannel.WHATSAPP)
                .contactValue(whatsappTo)
                .active(true)
                .build();
    }

    private String required(String key) {
        String value = System.getenv(key);
        if (value == null || value.isBlank()) {
            value = System.getProperty(key);
        }
        if (value == null || value.isBlank()) {
            throw new IllegalStateException("Missing required manual test setting: " + key);
        }
        return value;
    }
}
