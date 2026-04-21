package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class RobotPlantSideAnalysisDto {
    private String side;
    private String dominantState;
    private Integer evidenceCount;
}
