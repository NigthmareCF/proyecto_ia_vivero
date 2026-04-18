package com.vivero.module.robot.service;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotHeartbeatRequestDto;
import com.vivero.module.robot.dto.RobotObservationRequestDto;
import com.vivero.module.robot.dto.RobotObservationResponseDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import org.springframework.core.io.Resource;

/**
 * Contrato del módulo robot.
 */
public interface RobotService {

    RobotStatusResponseDto getCurrentStatus();

    RobotStatusResponseDto sendCommand(RobotCommandDto command);

    RobotStatusResponseDto applyManualControl(ManualControlDto control);

    RobotStatusResponseDto processHeartbeat(RobotHeartbeatRequestDto heartbeat);

    RobotObservationResponseDto registerObservation(RobotObservationRequestDto observation);

    Resource loadObservationImage(Long imageId);
}
