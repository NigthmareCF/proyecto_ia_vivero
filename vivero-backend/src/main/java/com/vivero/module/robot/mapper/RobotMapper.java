package com.vivero.module.robot.mapper;

import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.entity.RobotStatus;
import org.mapstruct.Mapper;

/**
 * Mapper del módulo robot.
 */
@Mapper(componentModel = "spring")
public interface RobotMapper {

    RobotStatusResponseDto toResponse(RobotStatus robotStatus);
}