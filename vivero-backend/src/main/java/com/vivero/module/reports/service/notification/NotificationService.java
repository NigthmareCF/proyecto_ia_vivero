package com.vivero.module.reports.service.notification;

import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.module.reports.entity.Report;
import com.vivero.shared.enums.NotificationChannel;

/**
 * Contrato para proveedores de notificación.
 */
public interface NotificationService {

    NotificationChannel getChannel();

    void sendReportNotification(Report report, NotificationConfig config, byte[] pdfContent);
}
