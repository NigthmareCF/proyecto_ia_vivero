package com.vivero.module.patrols.dto;

import com.vivero.shared.enums.PatrolFilter;
import com.vivero.shared.enums.PatrolMode;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO para iniciar un patrullaje.
 */
@Getter
@Setter
public class StartPatrolRequestDto {

    @NotNull(message = "Mode is required")
    private PatrolMode mode;

    @NotNull(message = "Filter is required")
    private PatrolFilter filter;
}