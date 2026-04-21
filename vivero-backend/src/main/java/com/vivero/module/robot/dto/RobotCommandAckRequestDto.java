package com.vivero.module.robot.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class RobotCommandAckRequestDto {

    @NotBlank(message = "Robot id is required")
    @Size(max = 80, message = "Robot id must not exceed 80 characters")
    private String robotId;
}
