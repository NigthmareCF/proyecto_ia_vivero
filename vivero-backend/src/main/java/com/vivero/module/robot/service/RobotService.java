package com.vivero.module.robot.service;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;

/**
 * Contrato del módulo robot.
 */
public interface RobotService {

    RobotStatusResponseDto getCurrentStatus();

    RobotStatusResponseDto sendCommand(RobotCommandDto command);

    RobotStatusResponseDto applyManualControl(ManualControlDto control);
}