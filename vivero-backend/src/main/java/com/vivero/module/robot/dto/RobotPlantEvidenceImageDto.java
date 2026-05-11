package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class RobotPlantEvidenceImageDto {
    private Long observationId;
    private Long imageId;
    private String imageUrl;
    private String mimeType;
    private Integer sortOrder;
    private boolean relevant;
    private String plantQr;
    private String plantSide;
    private String statusHint;
    private String finalState;
    private LocalDateTime observedAt;
}
