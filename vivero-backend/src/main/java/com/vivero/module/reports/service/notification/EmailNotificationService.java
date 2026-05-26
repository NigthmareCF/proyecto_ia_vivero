package com.vivero.module.reports.service.notification;

import com.vivero.config.AppProperties;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.exception.BusinessException;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.mail.MailAuthenticationException;
import org.springframework.mail.MailException;
import org.springframework.mail.MailSendException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class EmailNotificationService implements NotificationService {

    private final JavaMailSender mailSender;
    private final AppProperties appProperties;

    @Override
    public NotificationChannel getChannel() {
        return NotificationChannel.EMAIL;
    }

    @Override
    public void sendReportNotification(Report report, NotificationConfig config, byte[] pdfContent) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true);

            helper.setFrom(appProperties.getNotification().getEmail().getFrom());
            helper.setTo(config.getContactValue());
            helper.setSubject("Vivero report generated: " + report.getTitle());
            helper.setText(buildBody(report), false);
            helper.addAttachment("report-" + report.getId() + ".pdf", new ByteArrayResource(pdfContent));

            mailSender.send(message);
        } catch (MailAuthenticationException ex) {
            throw new BusinessException(
                    "Email provider rejected the configured credentials",
                    "EMAIL_PROVIDER_AUTH_FAILED",
                    ex
            );
        } catch (MailSendException ex) {
            throw new BusinessException(
                    "Email provider accepted the request but could not deliver the message",
                    "EMAIL_PROVIDER_SEND_FAILED",
                    ex
            );
        } catch (MessagingException ex) {
            throw new BusinessException(
                    "Email message could not be built correctly",
                    "EMAIL_MESSAGE_BUILD_FAILED",
                    ex
            );
        } catch (MailException ex) {
            throw new BusinessException(
                    "Email notification could not be sent by the configured provider",
                    "EMAIL_NOTIFICATION_ERROR",
                    ex
            );
        }
    }

    private String buildBody(Report report) {
        return """
                Report generated successfully.

                Title: %s
                Patrol ID: %d
                Summary: %s
                PDF path: %s
                """.formatted(
                report.getTitle(),
                report.getPatrolId(),
                report.getSummary() == null ? "No summary provided" : report.getSummary(),
                report.getPdfPath()
        );
    }
}
