package com.vivero.module.reports.service.notification;

import com.twilio.Twilio;
import com.twilio.rest.api.v2010.account.Message;
import com.twilio.type.PhoneNumber;
import com.vivero.config.AppProperties;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.format.DateTimeFormatter;

/**
 * Notificación por SMS usando Twilio.
 */
@Service
@RequiredArgsConstructor
public class SmsNotificationService implements NotificationService {

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private final AppProperties appProperties;

    @Override
    public NotificationChannel getChannel() {
        return NotificationChannel.SMS;
    }

    @Override
    public void sendReportNotification(Report report, NotificationConfig config, byte[] pdfContent) {
        String accountSid = appProperties.getNotification().getTwilio().getAccountSid();
        String authToken = appProperties.getNotification().getTwilio().getAuthToken();
        String messagingServiceSid = appProperties.getNotification().getTwilio().getMessagingServiceSid();
        String from = appProperties.getNotification().getTwilio().getFromSms();
        String to = resolveDestination(config);

        if (isBlank(accountSid) || isBlank(authToken) || (isBlank(from) && isBlank(messagingServiceSid))) {
            throw new BusinessException("Twilio SMS is not configured", "SMS_NOT_CONFIGURED");
        }
        if (isBlank(to)) {
            throw new BusinessException("User profile phone number is required for SMS", "PROFILE_PHONE_REQUIRED");
        }

        Twilio.init(accountSid, authToken);
        if (!isBlank(messagingServiceSid)) {
            Message.creator(
                            new PhoneNumber(to),
                            messagingServiceSid,
                            buildMessage(report)
                    )
                    .create();
            return;
        }

        Message.creator(
                        new PhoneNumber(to),
                        new PhoneNumber(from),
                        buildMessage(report)
                )
                .create();
    }

    private String buildMessage(Report report) {
        return "Reporte No." + report.getId()
                + "\nDetalles: " + safeSummary(report.getSummary())
                + "\nPatrullaje No." + report.getPatrolId()
                + "\nDeteccion de estados:"
                + "\nSano=" + safeCount(report.getHealthyCount())
                + "\nAtencion=" + safeCount(report.getAttentionCount())
                + "\nPeligro=" + safeCount(report.getDangerCount())
                + "\nObservaciones=" + safeCount(report.getObservationsCount())
                + "\nEmitido: " + formatCreatedAt(report)
                + "\nConsulta de reporte documentada y detallada: " + buildDownloadUrl(report);
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private String safeSummary(String value) {
        if (value == null || value.isBlank()) {
            return "sin resumen";
        }
        return value.trim();
    }

    private int safeCount(Integer value) {
        return value == null ? 0 : value;
    }

    private String formatCreatedAt(Report report) {
        if (report.getCreatedAt() == null) {
            return "sin fecha";
        }
        return DATE_FORMAT.format(report.getCreatedAt());
    }

    private String resolveDestination(NotificationConfig config) {
        if (config.getUser() != null && config.getUser().getPhoneNumber() != null && !config.getUser().getPhoneNumber().isBlank()) {
            return config.getUser().getPhoneNumber().trim();
        }
        return config.getContactValue();
    }

    private String buildDownloadUrl(Report report) {
        String baseUrl = appProperties.getPublicBaseUrl();
        if (baseUrl == null || baseUrl.isBlank()) {
            return "/reports/" + report.getId() + "/pdf";
        }
        return baseUrl.replaceAll("/+$", "") + "/reports/" + report.getId() + "/pdf";
    }
}
