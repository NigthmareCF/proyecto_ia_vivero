package com.vivero.module.robot.service.impl;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.entity.RobotStatus;
import com.vivero.module.robot.mapper.RobotMapper;
import com.vivero.module.robot.repository.RobotStatusRepository;
import com.vivero.module.robot.service.RobotService;
import com.vivero.shared.enums.RobotCommandType;
import com.vivero.shared.enums.RobotMode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Objects;

/**
 * Implementación del módulo robot.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RobotServiceImpl implements RobotService {

    private final RobotStatusRepository robotStatusRepository;
    private final RobotMapper robotMapper;

    @Override
    @Transactional(readOnly = true)
    public RobotStatusResponseDto getCurrentStatus() {
        return robotMapper.toResponse(getOrCreateStatus());
    }

    @Override
    @Transactional
    public RobotStatusResponseDto sendCommand(RobotCommandDto command) {
        RobotStatus status = getOrCreateStatus();

        switch (command.getCommandType()) {
            case START_PATROL -> status.setMode(RobotMode.AUTO);
            case STOP_PATROL -> status.setMode(RobotMode.IDLE);
            case GOTO_PLANT -> {
                status.setMode(RobotMode.GOTO);
                status.setCurrentPlantQr(normalizeQr(command.getTargetPlantQr()));
            }
            case SET_MODE -> {
                if (command.getTargetMode() != null) {
                    status.setMode(command.getTargetMode());
                }
            }
            case MANUAL_MOVE -> status.setMode(RobotMode.MANUAL);
            case HEARTBEAT -> { }
        }

        status.setConnected(true);
        status.setLastSeenAt(LocalDateTime.now());
        status.setLastCommand(command.getCommandType().name());

        robotStatusRepository.save(status);
        log.info("Comando robot procesado: {}", command.getCommandType());
        return robotMapper.toResponse(status);
    }

    @Override
    @Transactional
    public RobotStatusResponseDto applyManualControl(ManualControlDto control) {
        RobotStatus status = getOrCreateStatus();
        status.setMode(RobotMode.MANUAL);
        status.setConnected(true);
        status.setLastSeenAt(LocalDateTime.now());
        status.setLastCommand("MANUAL_" + control.getDirection().name());

        robotStatusRepository.save(status);
        log.info("Control manual aplicado: {}", control.getDirection());
        return robotMapper.toResponse(status);
    }

    private RobotStatus getOrCreateStatus() {
        return robotStatusRepository.findTopByOrderByLastSeenAtDesc()
                .orElseGet(() -> robotStatusRepository.save(Objects.requireNonNull(
                        RobotStatus.builder()
                                .mode(RobotMode.IDLE)
                                .connected(false)
                                .lastSeenAt(LocalDateTime.now())
                                .lastCommand("INIT")
                                .build()
                )));
    }

    private String normalizeQr(String qrCode) {
        if (qrCode == null || qrCode.trim().isEmpty()) {
            return null;
        }
        return qrCode.trim().toUpperCase();
    }
}