package com.vivero.module.robot.dto;

import com.vivero.shared.enums.RobotMode;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * DTO de salida del estado del robot.
 */
@Getter
@Builder
public class RobotStatusResponseDto {

    private Long id;
    private String robotId;
    private RobotMode mode;
    private Integer batteryLevel;
    private Double temperatureCelsius;
    private Double cpuUsagePercent;
    private String connectionQuality;
    private String currentPlantQr;
    private String currentPatrolId;
    private boolean connected;
    private boolean obstacleDetected;
    private boolean blocked;
    private boolean streamActive;
    private Integer queueDepth;
    private String statusSummary;
    private String activeCamera;
    private String controlProfile;
    private String speedProfile;
    private Integer currentSpeedPercent;
    private boolean rearObstacleDetected;
    private String lastWatchdogReason;
    private LocalDateTime lastSeenAt;
    private String lastCommand;
}
