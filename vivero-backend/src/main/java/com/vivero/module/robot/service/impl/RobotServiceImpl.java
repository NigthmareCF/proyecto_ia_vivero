package com.vivero.module.robot.service.impl;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotCommandAckRequestDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotHeartbeatRequestDto;
import com.vivero.module.robot.dto.RobotObservationImageResponseDto;
import com.vivero.module.robot.dto.RobotObservationRequestDto;
import com.vivero.module.robot.dto.RobotObservationResponseDto;
import com.vivero.module.robot.dto.RobotQueuedCommandResponseDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.entity.RobotObservation;
import com.vivero.module.robot.entity.RobotObservationImage;
import com.vivero.module.robot.entity.RobotQueuedCommand;
import com.vivero.module.robot.entity.RobotStatus;
import com.vivero.module.robot.mapper.RobotMapper;
import com.vivero.module.robot.repository.RobotObservationImageRepository;
import com.vivero.module.robot.repository.RobotObservationRepository;
import com.vivero.module.robot.repository.RobotQueuedCommandRepository;
import com.vivero.module.robot.repository.RobotStatusRepository;
import com.vivero.module.robot.service.RobotService;
import com.vivero.module.robot.service.support.RobotImageStorageService;
import com.vivero.shared.enums.RobotMode;
import com.vivero.shared.enums.RobotCommandType;
import com.vivero.shared.exception.ResourceNotFoundException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Implementación del módulo robot.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RobotServiceImpl implements RobotService {

    private final RobotStatusRepository robotStatusRepository;
    private final RobotObservationRepository robotObservationRepository;
    private final RobotObservationImageRepository robotObservationImageRepository;
    private final RobotQueuedCommandRepository robotQueuedCommandRepository;
    private final RobotMapper robotMapper;
    private final RobotImageStorageService robotImageStorageService;
    private final SimpMessagingTemplate messagingTemplate;
    private final ObjectMapper objectMapper;

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
            case START_PATROL -> {
                status.setMode(RobotMode.AUTO);
                status.setControlProfile("AUTO_LINE");
            }
            case STOP_PATROL -> {
                status.setMode(RobotMode.IDLE);
                status.setCurrentPlantQr(null);
                status.setBlocked(false);
                status.setControlProfile("SAFE_STOP");
            }
            case GOTO_PLANT -> {
                status.setMode(RobotMode.GOTO);
                status.setCurrentPlantQr(normalizeQr(command.getTargetPlantQr()));
            }
            case SET_MODE -> {
                if (command.getTargetMode() != null) {
                    status.setMode(command.getTargetMode());
                }
                status.setControlProfile(resolveControlProfile(command.getTargetMode(), status.getControlProfile()));
            }
            case MANUAL_MOVE -> {
                status.setMode(RobotMode.MANUAL);
                status.setControlProfile("MANUAL_FREE");
            }
            case SWITCH_CAMERA -> status.setActiveCamera(normalizeToken(command.getCameraName(), "FRONT"));
            case SET_SPEED_PROFILE -> status.setSpeedProfile(normalizeToken(command.getSpeedProfile(), status.getSpeedProfile()));
            case RUN_ACRO -> {
                status.setMode(RobotMode.MANUAL);
                status.setControlProfile("ACRO");
                status.setStatusSummary("Acrobacia: " + normalizeToken(command.getSequenceName(), "SPIN"));
            }
            case HEARTBEAT -> { }
        }

        status.setConnected(true);
        status.setLastSeenAt(LocalDateTime.now());
        status.setLastCommand(command.getCommandType().name());

        enqueueCommand(status.getRobotId(), command);
        robotStatusRepository.save(status);
        log.info("Comando robot procesado: {}", command.getCommandType());
        return publishStatus(status);
    }

    @Override
    @Transactional
    public RobotStatusResponseDto applyManualControl(ManualControlDto control) {
        RobotStatus status = getOrCreateStatus();
        status.setMode(RobotMode.MANUAL);
        status.setConnected(true);
        status.setStreamActive(true);
        status.setLastSeenAt(LocalDateTime.now());
        status.setLastCommand("MANUAL_" + control.getDirection().name());

        robotStatusRepository.save(status);
        log.info("Control manual aplicado: {}", control.getDirection());
        return publishStatus(status);
    }

    @Override
    @Transactional
    public RobotStatusResponseDto processHeartbeat(RobotHeartbeatRequestDto heartbeat) {
        RobotStatus status = getOrCreateStatus();
        status.setRobotId(heartbeat.getRobotId().trim());
        status.setMode(heartbeat.getMode());
        status.setBatteryLevel(heartbeat.getBatteryLevel());
        status.setTemperatureCelsius(heartbeat.getTemperatureCelsius());
        status.setCpuUsagePercent(heartbeat.getCpuUsagePercent());
        status.setConnectionQuality(normalizeBlank(heartbeat.getConnectionQuality()));
        status.setCurrentPlantQr(normalizeQr(heartbeat.getCurrentPlantQr()));
        status.setCurrentPatrolId(normalizeBlank(heartbeat.getCurrentPatrolId()));
        status.setObstacleDetected(heartbeat.isObstacleDetected());
        status.setBlocked(heartbeat.isBlocked());
        status.setStreamActive(heartbeat.isStreamActive());
        status.setQueueDepth(heartbeat.getQueueDepth());
        status.setStatusSummary(normalizeBlank(heartbeat.getStatusSummary()));
        status.setActiveCamera(normalizeToken(heartbeat.getActiveCamera(), status.getActiveCamera()));
        status.setControlProfile(normalizeToken(heartbeat.getControlProfile(), status.getControlProfile()));
        status.setSpeedProfile(normalizeToken(heartbeat.getSpeedProfile(), status.getSpeedProfile()));
        status.setConnected(true);
        status.setLastSeenAt(LocalDateTime.now());
        status.setLastCommand("HEARTBEAT");

        robotStatusRepository.save(status);
        log.debug("Heartbeat procesado para robot {}", status.getRobotId());
        return publishStatus(status);
    }

    @Override
    @Transactional
    public RobotObservationResponseDto registerObservation(RobotObservationRequestDto observation) {
        String robotId = observation.getRobotId().trim();
        List<RobotImageStorageService.StoredRobotImage> storedImages = robotImageStorageService.storeObservationImages(
                robotId,
                observation.getImagesBase64(),
                observation.getMimeType()
        );

        RobotObservation entity = robotObservationRepository.save(RobotObservation.builder()
                .robotId(robotId)
                .patrolId(normalizeBlank(observation.getPatrolId()))
                .plantQr(normalizeQr(observation.getPlantQr()))
                .captureReason(normalizeBlank(observation.getCaptureReason()))
                .statusHint(normalizeBlank(observation.getStatusHint()))
                .observedAt(observation.getObservedAt() != null ? observation.getObservedAt() : LocalDateTime.now())
                .imageCount(storedImages.size())
                .primaryImagePath(storedImages.get(0).filePath())
                .analysisStatus("PENDING_ANALYSIS")
                .build());

        List<RobotObservationImageResponseDto> images = new ArrayList<>();
        for (RobotImageStorageService.StoredRobotImage storedImage : storedImages) {
            RobotObservationImage savedImage = robotObservationImageRepository.save(RobotObservationImage.builder()
                    .observation(entity)
                    .filePath(storedImage.filePath())
                    .mimeType(storedImage.mimeType())
                    .sortOrder(storedImage.sortOrder())
                    .relevant(storedImage.sortOrder() == 0)
                    .build());
            images.add(toImageResponse(savedImage));
        }

        RobotObservationResponseDto response = RobotObservationResponseDto.builder()
                .id(entity.getId())
                .robotId(entity.getRobotId())
                .patrolId(entity.getPatrolId())
                .plantQr(entity.getPlantQr())
                .captureReason(entity.getCaptureReason())
                .statusHint(entity.getStatusHint())
                .analysisStatus(entity.getAnalysisStatus())
                .observedAt(entity.getObservedAt())
                .images(images)
                .build();

        messagingTemplate.convertAndSend("/topic/robot/observations", response);
        log.info("Observación registrada para planta {}", entity.getPlantQr());
        return response;
    }

    @Override
    @Transactional(readOnly = true)
    public RobotQueuedCommandResponseDto pollNextCommand(String robotId) {
        return robotQueuedCommandRepository.findTopByRobotIdAndAcknowledgedFalseOrderByCreatedAtAsc(robotId.trim())
                .map(this::toQueuedCommandResponse)
                .orElse(null);
    }

    @Override
    @Transactional
    public void acknowledgeCommand(Long commandId, RobotCommandAckRequestDto request) {
        RobotQueuedCommand command = robotQueuedCommandRepository.findById(commandId)
                .orElseThrow(() -> new ResourceNotFoundException("Robot queued command " + commandId + " not found"));
        if (!command.getRobotId().equalsIgnoreCase(request.getRobotId().trim())) {
            throw new ResourceNotFoundException("Robot queued command " + commandId + " does not belong to robot " + request.getRobotId());
        }
        command.setAcknowledged(true);
        command.setAcknowledgedAt(LocalDateTime.now());
        robotQueuedCommandRepository.save(command);
    }

    @Override
    @Transactional(readOnly = true)
    public Resource loadObservationImage(Long imageId) {
        RobotObservationImage image = robotObservationImageRepository.findById(imageId)
                .orElseThrow(() -> new ResourceNotFoundException("Robot observation image " + imageId + " not found"));
        FileSystemResource resource = new FileSystemResource(image.getFilePath());
        if (!resource.exists()) {
            throw new ResourceNotFoundException("Robot observation image file " + imageId + " not found on disk");
        }
        return resource;
    }

    private RobotStatus getOrCreateStatus() {
        return robotStatusRepository.findTopByOrderByLastSeenAtDesc()
                .orElseGet(() -> robotStatusRepository.save(Objects.requireNonNull(
                        RobotStatus.builder()
                                .robotId("ROBOT-001")
                                .mode(RobotMode.IDLE)
                                .connected(false)
                                .activeCamera("FRONT")
                                .controlProfile("IDLE")
                                .speedProfile("MEDIUM")
                                .lastSeenAt(LocalDateTime.now())
                                .lastCommand("INIT")
                                .build()
                )));
    }

    private RobotStatusResponseDto publishStatus(RobotStatus status) {
        RobotStatusResponseDto response = robotMapper.toResponse(status);
        messagingTemplate.convertAndSend("/topic/robot/status", response);
        return response;
    }

    private RobotObservationImageResponseDto toImageResponse(RobotObservationImage image) {
        return RobotObservationImageResponseDto.builder()
                .id(image.getId())
                .mimeType(image.getMimeType())
                .sortOrder(image.getSortOrder())
                .relevant(image.isRelevant())
                .imageUrl("/api/robot/observations/images/" + image.getId())
                .build();
    }

    private String normalizeQr(String qrCode) {
        if (qrCode == null || qrCode.trim().isEmpty()) {
            return null;
        }
        return qrCode.trim().toUpperCase();
    }

    private String normalizeBlank(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }

    private String normalizeToken(String value, String fallback) {
        if (value == null || value.trim().isEmpty()) {
            return fallback;
        }
        return value.trim().toUpperCase();
    }

    private String resolveControlProfile(RobotMode mode, String fallback) {
        if (mode == null) {
            return fallback;
        }
        return switch (mode) {
            case AUTO -> "AUTO_LINE";
            case MANUAL -> "MANUAL_FREE";
            case GOTO -> "GOTO";
            case IDLE -> "IDLE";
        };
    }

    private void enqueueCommand(String robotId, RobotCommandDto command) {
        try {
            RobotQueuedCommand queuedCommand = RobotQueuedCommand.builder()
                    .robotId(robotId)
                    .commandName(resolveRobotCommandName(command))
                    .payloadJson(objectMapper.writeValueAsString(resolveRobotCommandPayload(command)))
                    .build();
            robotQueuedCommandRepository.save(queuedCommand);
        } catch (Exception ex) {
            throw new IllegalStateException("Could not serialize robot command", ex);
        }
    }

    private String resolveRobotCommandName(RobotCommandDto command) {
        return switch (command.getCommandType()) {
            case START_PATROL -> "START_PATROL";
            case STOP_PATROL -> "STOP";
            case GOTO_PLANT -> "GOTO_PLANT";
            case SET_MODE -> resolveModeCommand(command.getTargetMode());
            case MANUAL_MOVE -> "MOVE";
            case SWITCH_CAMERA -> "CAMERA_SELECT";
            case SET_SPEED_PROFILE -> "SPEED_PROFILE";
            case RUN_ACRO -> "ACRO";
            case HEARTBEAT -> "HEARTBEAT";
        };
    }

    private Map<String, Object> resolveRobotCommandPayload(RobotCommandDto command) {
        Map<String, Object> payload = new LinkedHashMap<>();
        RobotCommandType commandType = command.getCommandType();
        if (commandType == RobotCommandType.MANUAL_MOVE) {
            payload.put("direction", command.getDirection() == null ? "stop" : command.getDirection().name().toLowerCase());
            payload.put("speed", command.getSpeed() == null ? 0 : command.getSpeed());
        } else if (commandType == RobotCommandType.GOTO_PLANT) {
            payload.put("plantQr", normalizeQr(command.getTargetPlantQr()));
        } else if (commandType == RobotCommandType.SWITCH_CAMERA) {
            payload.put("camera", normalizeBlank(command.getCameraName()));
        } else if (commandType == RobotCommandType.SET_SPEED_PROFILE) {
            payload.put("profile", normalizeToken(command.getSpeedProfile(), "MEDIUM"));
        } else if (commandType == RobotCommandType.RUN_ACRO) {
            payload.put("sequence", normalizeToken(command.getSequenceName(), "SPIN"));
        }
        return payload;
    }

    private String resolveModeCommand(RobotMode targetMode) {
        if (targetMode == null) {
            return "AUTO";
        }
        return switch (targetMode) {
            case AUTO -> "AUTO";
            case MANUAL -> "MANUAL_CONTROL";
            case GOTO -> "GOTO_PLANT";
            case IDLE -> "STOP";
        };
    }

    private RobotQueuedCommandResponseDto toQueuedCommandResponse(RobotQueuedCommand command) {
        try {
            return RobotQueuedCommandResponseDto.builder()
                    .id(command.getId())
                    .robotId(command.getRobotId())
                    .command(command.getCommandName())
                    .data(command.getPayloadJson() == null || command.getPayloadJson().isBlank()
                            ? Map.of()
                            : objectMapper.readValue(command.getPayloadJson(), new TypeReference<Map<String, Object>>() {}))
                    .createdAt(command.getCreatedAt())
                    .build();
        } catch (Exception ex) {
            throw new IllegalStateException("Could not deserialize robot command payload", ex);
        }
    }
}
