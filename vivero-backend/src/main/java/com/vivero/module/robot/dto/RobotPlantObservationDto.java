package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Builder
public class RobotPlantObservationDto {
    private Long observationId;
    private String plantQr;
    private String plantSide;
    private String statusHint;
    private String finalState;
    private String analysisStatus;
    private String analysisNotes;
    private LocalDateTime observedAt;
    private List<RobotObservationImageResponseDto> images;
}
