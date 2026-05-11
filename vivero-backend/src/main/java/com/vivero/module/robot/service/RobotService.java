package com.vivero.module.robot.service;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotCommandAckRequestDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotHeartbeatRequestDto;
import com.vivero.module.robot.dto.RobotObservationRequestDto;
import com.vivero.module.robot.dto.RobotObservationResponseDto;
import com.vivero.module.robot.dto.RobotPatrolAnalysisResponseDto;
import com.vivero.module.robot.dto.RobotQueuedCommandResponseDto;
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

    java.util.List<RobotObservationResponseDto> getObservationsByPatrol(String patrolId);

    RobotPatrolAnalysisResponseDto finalizePatrolAnalysis(String patrolId, String robotId);

    RobotPatrolAnalysisResponseDto getPatrolAnalysis(String patrolId);

    RobotQueuedCommandResponseDto pollNextCommand(String robotId);

    void acknowledgeCommand(Long commandId, RobotCommandAckRequestDto request);

    Resource loadObservationImage(Long imageId);
}
