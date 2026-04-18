package com.vivero.module.robot.dto;

import com.vivero.shared.enums.ManualDirection;
import com.vivero.shared.enums.RobotCommandType;
import com.vivero.shared.enums.RobotMode;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * DTO para comandos enviados al robot.
 */
@Getter
@Setter
public class RobotCommandDto {

    @NotNull(message = "Command type is required")
    private RobotCommandType commandType;

    private RobotMode targetMode;

    private ManualDirection direction;

    @Size(max = 120, message = "Target plant QR must not exceed 120 characters")
    private String targetPlantQr;

    @Min(value = 0, message = "Speed must be at least 0")
    @Max(value = 100, message = "Speed must be at most 100")
    private Integer speed;

    @Size(max = 40, message = "Camera name must not exceed 40 characters")
    private String cameraName;

    @Size(max = 40, message = "Speed profile must not exceed 40 characters")
    private String speedProfile;

    @Size(max = 80, message = "Sequence name must not exceed 80 characters")
    private String sequenceName;
}
