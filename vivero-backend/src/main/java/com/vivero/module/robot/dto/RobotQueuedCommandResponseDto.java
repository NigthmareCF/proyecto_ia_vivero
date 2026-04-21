package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.Map;

@Getter
@Builder
public class RobotQueuedCommandResponseDto {

    private Long id;
    private String robotId;
    private String command;
    private Map<String, Object> data;
    private LocalDateTime createdAt;
}
