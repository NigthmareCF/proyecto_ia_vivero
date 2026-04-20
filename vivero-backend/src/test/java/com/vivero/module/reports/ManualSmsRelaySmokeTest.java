package com.vivero.module.reports;

import com.vivero.config.AppProperties;
import com.vivero.module.auth.entity.User;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.module.reports.service.notification.SmsNotificationService;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.enums.UserRole;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assumptions.assumeTrue;

class ManualSmsRelaySmokeTest {

    @Test
    void shouldSendRealSmsThroughTwilioMessagingService() {
        assumeTrue(Boolean.getBoolean("manual.sms.test"), "Manual SMS smoke test disabled");

        String accountSid = required("TWILIO_ACCOUNT_SID");
        String authToken = required("TWILIO_AUTH_TOKEN");
        String messagingServiceSid = required("TWILIO_MESSAGING_SERVICE_SID");
        String smsTo = required("MANUAL_SMS_TO");

        AppProperties properties = new AppProperties();
        properties.getNotification().getTwilio().setAccountSid(accountSid);
        properties.getNotification().getTwilio().setAuthToken(authToken);
        properties.getNotification().getTwilio().setMessagingServiceSid(messagingServiceSid);

        SmsNotificationService smsNotificationService = new SmsNotificationService(properties);
        smsNotificationService.sendReportNotification(buildReport(), buildConfig(smsTo), new byte[0]);
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
                .title("Prueba SMS backend")
                .summary("Mensaje de prueba enviado desde el modulo reports del backend.")
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

    private NotificationConfig buildConfig(String smsTo) {
        return NotificationConfig.builder()
                .channel(NotificationChannel.SMS)
                .contactValue(smsTo)
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
