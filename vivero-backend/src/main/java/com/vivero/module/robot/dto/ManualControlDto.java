package com.vivero.module.robot.dto;

import com.vivero.shared.enums.ManualDirection;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO usado por WebSocket para control manual.
 */
@Getter
@Setter
public class ManualControlDto {

    @NotNull(message = "Direction is required")
    private ManualDirection direction;

    @Min(value = 0, message = "Speed must be at least 0")
    @Max(value = 100, message = "Speed must be at most 100")
    private Integer speed;
}