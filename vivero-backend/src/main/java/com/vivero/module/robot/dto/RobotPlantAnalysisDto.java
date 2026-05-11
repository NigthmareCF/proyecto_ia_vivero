package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.time.LocalDate;
import java.util.List;

@Getter
@Builder
public class RobotPlantAnalysisDto {
    private String patrolId;
    private String groupKey;
    private String plantNumber;
    private String potNumber;
    private String representativeExactQrLabel;
    private String plantGroupCode;
    private String representativePlantQr;
    private LocalDate operationalDate;
    private String finalState;
    private String summary;
    private Integer evidenceCount;
    private LocalDateTime lastObservedAt;
    private List<RobotPlantSideAnalysisDto> sides;
}
