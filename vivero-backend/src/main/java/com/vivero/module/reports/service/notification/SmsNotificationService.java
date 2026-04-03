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

/**
 * Notificación por SMS usando Twilio.
 */
@Service
@RequiredArgsConstructor
public class SmsNotificationService implements NotificationService {

    private final AppProperties appProperties;

    @Override
    public NotificationChannel getChannel() {
        return NotificationChannel.SMS;
    }

    @Override
    public void sendReportNotification(Report report, NotificationConfig config, byte[] pdfContent) {
        String accountSid = appProperties.getNotification().getTwilio().getAccountSid();
        String authToken = appProperties.getNotification().getTwilio().getAuthToken();
        String from = appProperties.getNotification().getTwilio().getFromSms();

        if (isBlank(accountSid) || isBlank(authToken) || isBlank(from)) {
            throw new BusinessException("Twilio SMS is not configured", "SMS_NOT_CONFIGURED");
        }

        Twilio.init(accountSid, authToken);
        Message.creator(
                        new PhoneNumber(config.getContactValue()),
                        new PhoneNumber(from),
                        buildMessage(report)
                )
                .create();
    }

    private String buildMessage(Report report) {
        return "Report " + report.getTitle() + " generated. PDF: " + report.getPdfPath();
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
