package com.vivero.module.reports.service.notification;

import com.vivero.config.AppProperties;
import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.shared.enums.NotificationChannel;
import com.vivero.shared.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

/**
 * Notificación por Telegram Bot API.
 */
@Service
@RequiredArgsConstructor
public class TelegramNotificationService implements NotificationService {

    private final AppProperties appProperties;
    private final HttpClient httpClient = HttpClient.newHttpClient();

    @Override
    public NotificationChannel getChannel() {
        return NotificationChannel.TELEGRAM;
    }

    @Override
    public void sendReportNotification(Report report, NotificationConfig config, byte[] pdfContent) {
        String botToken = appProperties.getNotification().getTelegram().getBotToken();

        if (botToken == null || botToken.isBlank()) {
            throw new BusinessException("Telegram bot is not configured", "TELEGRAM_NOT_CONFIGURED");
        }

        String text = URLEncoder.encode(buildMessage(report), StandardCharsets.UTF_8);
        String chatId = URLEncoder.encode(config.getContactValue(), StandardCharsets.UTF_8);
        URI uri = URI.create("https://api.telegram.org/bot" + botToken + "/sendMessage?chat_id=" + chatId + "&text=" + text);

        HttpRequest request = HttpRequest.newBuilder(uri).GET().build();
        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 400) {
                throw new BusinessException("Telegram notification failed", "TELEGRAM_NOTIFICATION_ERROR");
            }
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new BusinessException("Telegram notification failed", "TELEGRAM_NOTIFICATION_ERROR");
        } catch (IOException ex) {
            throw new BusinessException("Telegram notification failed", "TELEGRAM_NOTIFICATION_ERROR");
        }
    }

    private String buildMessage(Report report) {
        return "Report " + report.getTitle() + " generated. PDF path: " + report.getPdfPath();
    }
}
