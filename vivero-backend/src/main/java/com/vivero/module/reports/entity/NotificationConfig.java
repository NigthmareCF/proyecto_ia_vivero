package com.vivero.module.reports.entity;

import com.vivero.module.auth.entity.User;
import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.NotificationChannel;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Configuración de canales de notificación por usuario.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(
        name = "notification_config",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_notification_config_user_channel", columnNames = {"user_id", "channel"})
        }
)
public class NotificationConfig extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private NotificationChannel channel;

    @Column(name = "contact_value", nullable = false, length = 255)
    private String contactValue;

    @Builder.Default
    @Column(nullable = false)
    private boolean active = true;
}
