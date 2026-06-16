package com.vivero.module.robot.entity;

import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.RobotMode;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Estado persistido más reciente del robot.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "robot_status")
public class RobotStatus extends BaseEntity {

    @Column(name = "robot_id", nullable = false, length = 80)
    @Builder.Default
    private String robotId = "ROBOT-001";

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private RobotMode mode = RobotMode.IDLE;

    @Column(name = "battery_level")
    private Integer batteryLevel;

    @Column(name = "current_plant_qr", length = 120)
    private String currentPlantQr;

    @Column(name = "current_patrol_id", length = 80)
    private String currentPatrolId;

    @Column(name = "is_connected", nullable = false)
    @Builder.Default
    private boolean connected = false;

    @Column(name = "temperature_celsius")
    private Double temperatureCelsius;

    @Column(name = "cpu_usage_percent")
    private Double cpuUsagePercent;

    @Column(name = "connection_quality", length = 40)
    private String connectionQuality;

    @Column(name = "obstacle_detected", nullable = false)
    @Builder.Default
    private boolean obstacleDetected = false;

    @Column(name = "is_blocked", nullable = false)
    @Builder.Default
    private boolean blocked = false;

    @Column(name = "stream_active", nullable = false)
    @Builder.Default
    private boolean streamActive = false;

    @Column(name = "queue_depth")
    private Integer queueDepth;

    @Column(name = "status_summary", length = 255)
    private String statusSummary;

    @Column(name = "active_camera", length = 40)
    private String activeCamera;

    @Column(name = "control_profile", length = 40)
    private String controlProfile;

    @Column(name = "speed_profile", length = 40)
    private String speedProfile;

    @Column(name = "stream_profile", length = 40)
    private String streamProfile;

    @Column(name = "current_speed_percent")
    private Integer currentSpeedPercent;

    @Column(name = "estimated_speed_mps")
    private Double estimatedSpeedMps;

    @Column(name = "imu_heading_deg")
    private Double imuHeadingDeg;

    @Column(name = "rear_obstacle_detected", nullable = false)
    @Builder.Default
    private boolean rearObstacleDetected = false;

    @Column(name = "last_watchdog_reason", length = 120)
    private String lastWatchdogReason;

    @Column(name = "last_seen_at", nullable = false)
    private LocalDateTime lastSeenAt;

    @Column(name = "last_command", length = 40)
    private String lastCommand;
}
