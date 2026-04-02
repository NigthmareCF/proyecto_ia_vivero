package com.vivero.module.patrols.dto;

import com.vivero.shared.enums.PatrolFilter;
import com.vivero.shared.enums.PatrolMode;
import com.vivero.shared.enums.PatrolStatus;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * DTO de salida para patrullajes.
 */
@Getter
@Builder
public class PatrolResponseDto {

    private Long id;
    private String startedByEmail;
    private String startedByName;
    private PatrolMode mode;
    private PatrolFilter filter;
    private PatrolStatus status;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private int observationsCount;
}