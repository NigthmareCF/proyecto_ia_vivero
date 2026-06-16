package com.vivero.module.robot.dto;

import com.vivero.shared.enums.RobotMode;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * Telemetría periódica enviada por la Raspberry Pi.
 */
@Getter
@Setter
public class RobotHeartbeatRequestDto {

    @NotBlank(message = "Robot id is required")
    @Size(max = 80, message = "Robot id must not exceed 80 characters")
    private String robotId;

    @NotNull(message = "Mode is required")
    private RobotMode mode;

    @Min(value = 0, message = "Battery level must be at least 0")
    @Max(value = 100, message = "Battery level must be at most 100")
    private Integer batteryLevel;

    private Double temperatureCelsius;

    private Double cpuUsagePercent;

    @Size(max = 40, message = "Connection quality must not exceed 40 characters")
    private String connectionQuality;

    @Size(max = 120, message = "Current plant QR must not exceed 120 characters")
    private String currentPlantQr;

    @Size(max = 80, message = "Current patrol id must not exceed 80 characters")
    private String currentPatrolId;

    private boolean obstacleDetected;

    private boolean blocked;

    private boolean streamActive;

    @Min(value = 0, message = "Queue depth must be at least 0")
    private Integer queueDepth;

    @Size(max = 255, message = "Status summary must not exceed 255 characters")
    private String statusSummary;

    @Size(max = 40, message = "Active camera must not exceed 40 characters")
    private String activeCamera;

    @Size(max = 40, message = "Control profile must not exceed 40 characters")
    private String controlProfile;

    @Size(max = 40, message = "Speed profile must not exceed 40 characters")
    private String speedProfile;

    @Size(max = 40, message = "Stream profile must not exceed 40 characters")
    private String streamProfile;

    @Min(value = 0, message = "Current speed must be at least 0")
    @Max(value = 100, message = "Current speed must be at most 100")
    private Integer currentSpeedPercent;

    private Double estimatedSpeedMps;

    private Double imuHeadingDeg;

    private boolean rearObstacleDetected;

    @Size(max = 120, message = "Last watchdog reason must not exceed 120 characters")
    private String lastWatchdogReason;
}
