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
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

/**
 * Notificación por correo electrónico con el PDF adjunto.
 */
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
            helper.setText(buildBody(report));
            helper.addAttachment("report-" + report.getId() + ".pdf", new ByteArrayResource(pdfContent));

            mailSender.send(message);
        } catch (MessagingException ex) {
            throw new BusinessException("Failed to send email notification", "EMAIL_NOTIFICATION_ERROR");
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
