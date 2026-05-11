package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.time.LocalDate;
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
    private String exactQrLabel;
    private String groupKey;
    private String plantNumber;
    private String potNumber;
    private String plantQr;
    private String plantGroupCode;
    private String plantSide;
    private String captureReason;
    private String statusHint;
    private LocalDate operationalDate;
    private Integer scanSequence;
    private String analysisStatus;
    private String finalState;
    private String analysisNotes;
    private LocalDateTime observedAt;
    private List<RobotObservationImageResponseDto> images;
}
