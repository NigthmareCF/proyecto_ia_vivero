package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
public class RobotPatrolAnalysisResponseDto {
    private String robotId;
    private String patrolId;
    private Integer totalGroups;
    private Integer healthyCount;
    private Integer attentionCount;
    private Integer dangerCount;
    private Integer manualReviewCount;
    private Integer inconclusiveCount;
    private List<RobotPlantAnalysisDto> plants;
}
