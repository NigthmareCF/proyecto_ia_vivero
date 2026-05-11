package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Builder
public class RobotPlantAnalysisDto {
    private String patrolId;
    private String plantGroupCode;
    private String representativePlantQr;
    private String finalState;
    private String summary;
    private Integer evidenceCount;
    private LocalDateTime lastObservedAt;
    private List<RobotPlantSideAnalysisDto> sides;
    private List<RobotPlantEvidenceImageDto> evidenceImages;
    private List<RobotPlantObservationDto> observations;
}
