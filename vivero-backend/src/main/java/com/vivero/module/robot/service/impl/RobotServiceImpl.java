package com.vivero.module.robot.service.impl;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotCommandAckRequestDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotHeartbeatRequestDto;
import com.vivero.module.robot.dto.RobotObservationImageResponseDto;
import com.vivero.module.robot.dto.RobotObservationRequestDto;
import com.vivero.module.robot.dto.RobotObservationResponseDto;
import com.vivero.module.robot.dto.RobotPatrolAnalysisResponseDto;
import com.vivero.module.robot.dto.RobotPlantAnalysisDto;
import com.vivero.module.robot.dto.RobotPlantEvidenceImageDto;
import com.vivero.module.robot.dto.RobotPlantObservationDto;
import com.vivero.module.robot.dto.RobotPlantSideAnalysisDto;
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
import com.vivero.shared.enums.RobotCommandType;
import com.vivero.shared.enums.RobotMode;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

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
        return robotMapper.toResponse(
                robotStatusRepository.findTopByOrderByLastSeenAtDesc()
                        .orElseGet(this::buildDefaultStatus)
        );
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
        status.setCurrentSpeedPercent(heartbeat.getCurrentSpeedPercent());
        status.setEstimatedSpeedMps(heartbeat.getEstimatedSpeedMps());
        status.setImuHeadingDeg(heartbeat.getImuHeadingDeg());
        status.setRearObstacleDetected(heartbeat.isRearObstacleDetected());
        status.setLastWatchdogReason(normalizeBlank(heartbeat.getLastWatchdogReason()));
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

        String normalizedQr = normalizeQr(observation.getPlantQr());
        ParsedQr parsedQr = parseQr(normalizedQr);

        RobotObservation entity = robotObservationRepository.save(RobotObservation.builder()
                .robotId(robotId)
                .patrolId(normalizeBlank(observation.getPatrolId()))
                .plantQr(normalizedQr)
                .plantGroupCode(parsedQr.groupCode())
                .plantSide(parsedQr.side())
                .captureReason(normalizeBlank(observation.getCaptureReason()))
                .statusHint(normalizeBlank(observation.getStatusHint()))
                .observedAt(observation.getObservedAt() != null ? observation.getObservedAt() : LocalDateTime.now())
                .imageCount(storedImages.size())
                .primaryImagePath(storedImages.get(0).filePath())
                .analysisStatus("PENDING_ANALYSIS")
                .finalState(null)
                .analysisNotes(null)
                .build());

        List<RobotObservationImageResponseDto> images = new ArrayList<>();
        Set<Integer> relevantSortOrders = resolveRelevantSortOrders(
                normalizeObservationState(observation.getStatusHint()),
                storedImages.size()
        );
        for (RobotImageStorageService.StoredRobotImage storedImage : storedImages) {
            RobotObservationImage savedImage = robotObservationImageRepository.save(RobotObservationImage.builder()
                    .observation(entity)
                    .filePath(storedImage.filePath())
                    .mimeType(storedImage.mimeType())
                    .sortOrder(storedImage.sortOrder())
                    .relevant(relevantSortOrders.contains(storedImage.sortOrder()))
                    .build());
            images.add(toImageResponse(savedImage));
        }

        RobotObservationResponseDto response = RobotObservationResponseDto.builder()
                .id(entity.getId())
                .robotId(entity.getRobotId())
                .patrolId(entity.getPatrolId())
                .plantQr(entity.getPlantQr())
                .plantGroupCode(entity.getPlantGroupCode())
                .plantSide(entity.getPlantSide())
                .captureReason(entity.getCaptureReason())
                .statusHint(entity.getStatusHint())
                .analysisStatus(entity.getAnalysisStatus())
                .finalState(entity.getFinalState())
                .analysisNotes(entity.getAnalysisNotes())
                .observedAt(entity.getObservedAt())
                .images(images)
                .build();

        messagingTemplate.convertAndSend("/topic/robot/observations", response);
        log.info("Observación registrada para planta {}", entity.getPlantQr());
        return response;
    }

    @Override
    @Transactional
    public RobotPatrolAnalysisResponseDto finalizePatrolAnalysis(String patrolId, String robotId) {
        RobotPatrolAnalysisResponseDto analysis = buildPatrolAnalysis(patrolId, robotId, true);
        messagingTemplate.convertAndSend("/topic/robot/patrol-analysis", analysis);
        return analysis;
    }

    @Override
    @Transactional(readOnly = true)
    public RobotPatrolAnalysisResponseDto getPatrolAnalysis(String patrolId) {
        String robotId = robotStatusRepository.findTopByOrderByLastSeenAtDesc()
                .map(RobotStatus::getRobotId)
                .orElse("ROBOT-001");
        return buildPatrolAnalysis(patrolId, robotId, false);
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

    private RobotPatrolAnalysisResponseDto buildPatrolAnalysis(String patrolId, String robotId, boolean persistResults) {
        List<RobotObservation> observations = robotObservationRepository.findByPatrolIdOrderByObservedAtAsc(patrolId);
        if (observations.isEmpty()) {
            throw new ResourceNotFoundException("No robot observations found for patrol " + patrolId);
        }

        Map<String, List<RobotObservation>> grouped = observations.stream()
                .collect(Collectors.groupingBy(
                        observation -> normalizeToken(observation.getPlantGroupCode(), normalizeQr(observation.getPlantQr())),
                        LinkedHashMap::new,
                        Collectors.toList()
                ));

        List<RobotPlantAnalysisDto> plantAnalyses = new ArrayList<>();
        int healthy = 0;
        int attention = 0;
        int danger = 0;
        int manualReview = 0;
        int inconclusive = 0;

        for (Map.Entry<String, List<RobotObservation>> entry : grouped.entrySet()) {
            List<RobotObservation> groupObservations = entry.getValue();
            groupObservations.sort(Comparator.comparing(RobotObservation::getObservedAt));
            String finalState = resolveFinalState(groupObservations);
            String summary = buildPlantSummary(entry.getKey(), finalState, groupObservations.size());
            LocalDateTime lastObservedAt = groupObservations.get(groupObservations.size() - 1).getObservedAt();
            List<RobotPlantObservationDto> observationDtos = groupObservations.stream()
                    .map(observation -> toPlantObservation(observation, finalState))
                    .toList();
            List<RobotPlantEvidenceImageDto> evidenceImages = observationDtos.stream()
                    .flatMap(observation -> observation.getImages().stream()
                            .map(image -> RobotPlantEvidenceImageDto.builder()
                                    .observationId(observation.getObservationId())
                                    .imageId(image.getId())
                                    .imageUrl(image.getImageUrl())
                                    .mimeType(image.getMimeType())
                                    .sortOrder(image.getSortOrder())
                                    .relevant(image.isRelevant())
                                    .plantQr(observation.getPlantQr())
                                    .plantSide(observation.getPlantSide())
                                    .statusHint(observation.getStatusHint())
                                    .finalState(observation.getFinalState())
                                    .observedAt(observation.getObservedAt())
                                    .build()))
                    .sorted(Comparator
                            .comparing(RobotPlantEvidenceImageDto::isRelevant).reversed()
                            .thenComparing(RobotPlantEvidenceImageDto::getObservedAt, Comparator.nullsLast(Comparator.reverseOrder()))
                            .thenComparing(RobotPlantEvidenceImageDto::getSortOrder, Comparator.nullsLast(Comparator.naturalOrder())))
                    .toList();

            if (persistResults) {
                for (RobotObservation observation : groupObservations) {
                    observation.setAnalysisStatus("FINALIZED");
                    observation.setFinalState(finalState);
                    observation.setAnalysisNotes(summary);
                    robotObservationRepository.save(observation);
                }
                enqueuePlantStateUpdate(robotId, patrolId, entry.getKey(), groupObservations.get(0).getPlantQr(), finalState, summary);
            }

            List<RobotPlantSideAnalysisDto> sides = groupObservations.stream()
                    .collect(Collectors.groupingBy(
                            observation -> normalizeToken(observation.getPlantSide(), "SIN_LADO"),
                            LinkedHashMap::new,
                            Collectors.toList()
                    ))
                    .entrySet()
                    .stream()
                    .map(sideEntry -> RobotPlantSideAnalysisDto.builder()
                            .side(sideEntry.getKey())
                            .dominantState(resolveFinalState(sideEntry.getValue()))
                            .evidenceCount(sideEntry.getValue().size())
                            .build())
                    .toList();

            plantAnalyses.add(RobotPlantAnalysisDto.builder()
                    .patrolId(patrolId)
                    .plantGroupCode(entry.getKey())
                    .representativePlantQr(groupObservations.get(0).getPlantQr())
                    .finalState(finalState)
                    .summary(summary)
                    .evidenceCount(groupObservations.size())
                    .lastObservedAt(lastObservedAt)
                    .sides(sides)
                    .evidenceImages(evidenceImages)
                    .observations(observationDtos)
                    .build());

            switch (finalState) {
                case "SANO" -> healthy++;
                case "ATENCION" -> attention++;
                case "PELIGRO" -> danger++;
                case "REVISION_MANUAL" -> manualReview++;
                default -> inconclusive++;
            }
        }

        return RobotPatrolAnalysisResponseDto.builder()
                .robotId(robotId)
                .patrolId(patrolId)
                .totalGroups(plantAnalyses.size())
                .healthyCount(healthy)
                .attentionCount(attention)
                .dangerCount(danger)
                .manualReviewCount(manualReview)
                .inconclusiveCount(inconclusive)
                .plants(plantAnalyses)
                .build();
    }

    private RobotStatus getOrCreateStatus() {
        return robotStatusRepository.findTopByOrderByLastSeenAtDesc()
                .orElseGet(() -> robotStatusRepository.save(Objects.requireNonNull(buildDefaultStatus())));
    }

    private RobotStatus buildDefaultStatus() {
        return RobotStatus.builder()
                .robotId("ROBOT-001")
                .mode(RobotMode.IDLE)
                .connected(false)
                .batteryLevel(0)
                .queueDepth(0)
                .streamActive(false)
                .obstacleDetected(false)
                .blocked(false)
                .connectionQuality("OFFLINE")
                .statusSummary("Sin telemetria disponible. Esperando heartbeat de la Pi 5.")
                .activeCamera("FRONT")
                .controlProfile("IDLE")
                .speedProfile("MEDIUM")
                .currentSpeedPercent(null)
                .estimatedSpeedMps(null)
                .imuHeadingDeg(null)
                .rearObstacleDetected(false)
                .lastWatchdogReason(null)
                .lastSeenAt(LocalDateTime.now())
                .lastCommand("INIT")
                .build();
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

    private RobotPlantObservationDto toPlantObservation(RobotObservation observation, String finalState) {
        List<RobotObservationImageResponseDto> images = robotObservationImageRepository
                .findByObservationIdOrderBySortOrderAsc(observation.getId())
                .stream()
                .map(this::toImageResponse)
                .toList();

        return RobotPlantObservationDto.builder()
                .observationId(observation.getId())
                .plantQr(observation.getPlantQr())
                .plantSide(observation.getPlantSide())
                .statusHint(normalizeObservationState(observation.getStatusHint()))
                .finalState(finalState)
                .analysisStatus(observation.getAnalysisStatus())
                .analysisNotes(observation.getAnalysisNotes())
                .observedAt(observation.getObservedAt())
                .images(images)
                .build();
    }

    private String normalizeQr(String qrCode) {
        if (qrCode == null || qrCode.trim().isEmpty()) {
            return null;
        }
        return qrCode.trim().toUpperCase(Locale.ROOT);
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
        return value.trim().toUpperCase(Locale.ROOT);
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

    private void enqueuePlantStateUpdate(
            String robotId,
            String patrolId,
            String plantGroupCode,
            String plantQr,
            String finalState,
            String summary
    ) {
        try {
            Map<String, Object> payload = new LinkedHashMap<>();
            payload.put("patrolId", patrolId);
            payload.put("plantGroupCode", plantGroupCode);
            payload.put("plantQr", plantQr);
            payload.put("state", finalState);
            payload.put("summary", summary);

            robotQueuedCommandRepository.save(RobotQueuedCommand.builder()
                    .robotId(robotId)
                    .commandName("PLANT_STATE_UPDATE")
                    .payloadJson(objectMapper.writeValueAsString(payload))
                    .build());
        } catch (Exception ex) {
            throw new IllegalStateException("Could not serialize plant state update", ex);
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
            payload.put("direction", command.getDirection() == null ? "stop" : command.getDirection().name().toLowerCase(Locale.ROOT));
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
                            : objectMapper.readValue(command.getPayloadJson(), new TypeReference<Map<String, Object>>() { }))
                    .createdAt(command.getCreatedAt())
                    .build();
        } catch (Exception ex) {
            throw new IllegalStateException("Could not deserialize robot command payload", ex);
        }
    }

    private String resolveFinalState(List<RobotObservation> observations) {
        List<String> states = observations.stream()
                .map(RobotObservation::getStatusHint)
                .map(this::normalizeObservationState)
                .toList();
        if (states.stream().anyMatch("PELIGRO"::equals)) {
            return "PELIGRO";
        }
        if (states.stream().anyMatch("ATENCION"::equals)) {
            return "ATENCION";
        }
        if (states.stream().anyMatch("REVISION_MANUAL"::equals)) {
            return "REVISION_MANUAL";
        }
        if (states.stream().anyMatch("INCONCLUSA"::equals)) {
            return "INCONCLUSA";
        }
        return "SANO";
    }

    private String normalizeObservationState(String rawState) {
        String value = normalizeToken(rawState, "INCONCLUSA");
        return switch (value) {
            case "HEALTHY", "SANO" -> "SANO";
            case "ATTENTION", "ATENCION" -> "ATENCION";
            case "DANGER", "PELIGRO" -> "PELIGRO";
            case "REVISION", "REVISION_MANUAL", "MANUAL_REVIEW" -> "REVISION_MANUAL";
            default -> "INCONCLUSA";
        };
    }

    private String buildPlantSummary(String plantGroupCode, String finalState, int evidenceCount) {
        return "Grupo " + plantGroupCode
                + " consolidado en estado " + finalState
                + " con " + evidenceCount + " evidencias capturadas durante el patrullaje.";
    }

    private Set<Integer> resolveRelevantSortOrders(String normalizedState, int imageCount) {
        if (imageCount <= 0) {
            return Set.of();
        }
        if ("PELIGRO".equals(normalizedState)) {
            return buildRelevantSortOrderSet(Math.min(imageCount, 3));
        }
        if ("ATENCION".equals(normalizedState) || "REVISION_MANUAL".equals(normalizedState)) {
            return buildRelevantSortOrderSet(Math.min(imageCount, 2));
        }
        return Set.of(0);
    }

    private Set<Integer> buildRelevantSortOrderSet(int count) {
        return IntStream.range(0, Math.max(count, 1))
                .boxed()
                .collect(Collectors.toSet());
    }

    private ParsedQr parseQr(String plantQr) {
        if (plantQr == null || plantQr.isBlank()) {
            return new ParsedQr("UNKNOWN", "NA");
        }
        String[] parts = plantQr.split("_");
        if (parts.length >= 5 && "PLA".equals(parts[0]) && "MA".equals(parts[2])) {
            String groupCode = String.join("_", parts[0], parts[1], parts[2], parts[3]);
            String side = normalizePlantSide(parts[4]);
            return new ParsedQr(groupCode, side);
        }
        if (parts.length >= 5 && "PLA".equals(parts[0]) && "M".equals(parts[2])) {
            String groupCode = String.join("_", parts[0], parts[1], parts[2], parts[3]);
            String side = normalizePlantSide(parts[4]);
            return new ParsedQr(groupCode, side);
        }
        return new ParsedQr(plantQr, "NA");
    }

    private String normalizePlantSide(String rawSide) {
        String side = normalizeToken(rawSide, "NA");
        return switch (side) {
            case "D", "DER", "DERECHA", "RIGHT" -> "D";
            case "I", "IZQ", "IZQUIERDA", "LEFT" -> "I";
            case "O", "CENTER", "CENTRO" -> "O";
            default -> side;
        };
    }

    private record ParsedQr(String groupCode, String side) {}
}
