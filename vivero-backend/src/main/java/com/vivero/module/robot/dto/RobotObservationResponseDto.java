package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Respuesta de observación almacenada.
 */
@Getter
@Builder
public class RobotObservationResponseDto {

    private Long id;
    private String robotId;
    private String patrolId;
    private String plantQr;
    private String captureReason;
    private String statusHint;
    private String analysisStatus;
    private LocalDateTime observedAt;
    private List<RobotObservationImageResponseDto> images;
}
