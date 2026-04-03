package com.vivero.module.reports.repository;

import com.vivero.module.reports.entity.NotificationConfig;
import com.vivero.shared.enums.NotificationChannel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repositorio de configuraciones de notificación por usuario.
 */
@Repository
public interface NotificationConfigRepository extends JpaRepository<NotificationConfig, Long> {

    List<NotificationConfig> findByUserIdOrderByChannelAsc(Long userId);

    List<NotificationConfig> findByUserIdAndActiveTrue(Long userId);

    Optional<NotificationConfig> findByUserIdAndChannel(Long userId, NotificationChannel channel);
}
