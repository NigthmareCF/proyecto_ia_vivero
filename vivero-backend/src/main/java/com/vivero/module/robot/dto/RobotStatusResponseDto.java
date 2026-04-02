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
    private RobotMode mode;
    private Integer batteryLevel;
    private String currentPlantQr;
    private boolean connected;
    private LocalDateTime lastSeenAt;
    private String lastCommand;
}