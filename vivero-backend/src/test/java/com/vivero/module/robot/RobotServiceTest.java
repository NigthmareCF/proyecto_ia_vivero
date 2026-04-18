package com.vivero.module.robot;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotHeartbeatRequestDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.entity.RobotStatus;
import com.vivero.module.robot.mapper.RobotMapper;
import com.vivero.module.robot.repository.RobotObservationImageRepository;
import com.vivero.module.robot.repository.RobotObservationRepository;
import com.vivero.module.robot.repository.RobotStatusRepository;
import com.vivero.module.robot.service.impl.RobotServiceImpl;
import com.vivero.module.robot.service.support.RobotImageStorageService;
import com.vivero.shared.enums.ManualDirection;
import com.vivero.shared.enums.RobotCommandType;
import com.vivero.shared.enums.RobotMode;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mapstruct.factory.Mappers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.time.LocalDateTime;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RobotServiceTest {

    @Mock
    private RobotStatusRepository robotStatusRepository;
    @Mock
    private RobotObservationRepository robotObservationRepository;
    @Mock
    private RobotObservationImageRepository robotObservationImageRepository;
    @Mock
    private RobotImageStorageService robotImageStorageService;
    @Mock
    private SimpMessagingTemplate messagingTemplate;

    private RobotServiceImpl robotService;

    @BeforeEach
    void setUp() {
        RobotMapper robotMapper = Mappers.getMapper(RobotMapper.class);
        robotService = new RobotServiceImpl(
                robotStatusRepository,
                robotObservationRepository,
                robotObservationImageRepository,
                robotMapper,
                robotImageStorageService,
                messagingTemplate
        );
    }

    @Test
    void sendGotoCommandShouldUpdateModeAndPlantQr() {
        RobotStatus status = RobotStatus.builder()
                .mode(RobotMode.IDLE)
                .connected(true)
                .lastSeenAt(LocalDateTime.now())
                .lastCommand("INIT")
                .build();

        RobotCommandDto command = new RobotCommandDto();
        command.setCommandType(RobotCommandType.GOTO_PLANT);
        command.setTargetPlantQr(" qr-009 ");

        when(robotStatusRepository.findTopByOrderByLastSeenAtDesc()).thenReturn(Optional.of(status));
        when(robotStatusRepository.save(any(RobotStatus.class))).thenAnswer(invocation -> invocation.getArgument(0, RobotStatus.class));

        RobotStatusResponseDto response = robotService.sendCommand(command);

        assertEquals(RobotMode.GOTO, response.getMode());
        assertEquals("QR-009", response.getCurrentPlantQr());
        assertEquals("GOTO_PLANT", response.getLastCommand());
        verify(robotStatusRepository).save(any(RobotStatus.class));
    }

    @Test
    void applyManualControlShouldSwitchRobotToManual() {
        RobotStatus status = RobotStatus.builder()
                .mode(RobotMode.IDLE)
                .connected(false)
                .lastSeenAt(LocalDateTime.now())
                .lastCommand("INIT")
                .build();

        ManualControlDto control = new ManualControlDto();
        control.setDirection(ManualDirection.LEFT);
        control.setSpeed(70);

        when(robotStatusRepository.findTopByOrderByLastSeenAtDesc()).thenReturn(Optional.of(status));
        when(robotStatusRepository.save(any(RobotStatus.class))).thenAnswer(invocation -> invocation.getArgument(0, RobotStatus.class));

        RobotStatusResponseDto response = robotService.applyManualControl(control);

        assertEquals(RobotMode.MANUAL, response.getMode());
        assertEquals("MANUAL_LEFT", response.getLastCommand());
        verify(robotStatusRepository).save(any(RobotStatus.class));
    }

    @Test
    void processHeartbeatShouldUpdateTelemetryFields() {
        RobotStatus status = RobotStatus.builder()
                .robotId("ROBOT-001")
                .mode(RobotMode.IDLE)
                .connected(false)
                .lastSeenAt(LocalDateTime.now())
                .lastCommand("INIT")
                .build();

        RobotHeartbeatRequestDto heartbeat = new RobotHeartbeatRequestDto();
        heartbeat.setRobotId("ROBOT-PI-05");
        heartbeat.setMode(RobotMode.AUTO);
        heartbeat.setBatteryLevel(82);
        heartbeat.setTemperatureCelsius(51.4);
        heartbeat.setCpuUsagePercent(37.8);
        heartbeat.setConnectionQuality("GOOD");
        heartbeat.setCurrentPlantQr("plant-011");
        heartbeat.setCurrentPatrolId("patrol-1");
        heartbeat.setObstacleDetected(true);
        heartbeat.setBlocked(false);
        heartbeat.setStreamActive(true);
        heartbeat.setQueueDepth(3);
        heartbeat.setStatusSummary("Recorrido estable");

        when(robotStatusRepository.findTopByOrderByLastSeenAtDesc()).thenReturn(Optional.of(status));
        when(robotStatusRepository.save(any(RobotStatus.class))).thenAnswer(invocation -> invocation.getArgument(0, RobotStatus.class));

        RobotStatusResponseDto response = robotService.processHeartbeat(heartbeat);

        assertEquals("ROBOT-PI-05", response.getRobotId());
        assertEquals(RobotMode.AUTO, response.getMode());
        assertEquals(82, response.getBatteryLevel());
        assertEquals("PLANT-011", response.getCurrentPlantQr());
        assertEquals("patrol-1", response.getCurrentPatrolId());
        assertEquals("GOOD", response.getConnectionQuality());
        verify(robotStatusRepository).save(any(RobotStatus.class));
    }
}
