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
import com.vivero.shared.enums.SearchStartOrientation;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

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
            case SEARCH_BY_STATE -> {
                status.setMode(RobotMode.AUTO);
                status.setControlProfile("SEARCH_BY_STATE");
                status.setStatusSummary("Busqueda por estado: " + normalizeToken(command.getRequestedState(), "ATENCION"));
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

        String normalizedQr = normalizeQr(observation.getPlantQr());
        ParsedQr parsedQr = parseQr(normalizedQr);
        LocalDateTime observedAt = observation.getObservedAt() != null ? observation.getObservedAt() : LocalDateTime.now();
        LocalDate operationalDate = observedAt.toLocalDate();
        String patrolId = normalizeBlank(observation.getPatrolId());
        int scanSequence = resolveNextScanSequence(patrolId, operationalDate);

        RobotObservation entity = robotObservationRepository.save(RobotObservation.builder()
                .robotId(robotId)
                .patrolId(patrolId)
                .plantQr(normalizedQr)
                .plantGroupCode(parsedQr.groupCode())
                .plantSide(parsedQr.side())
                .captureReason(normalizeBlank(observation.getCaptureReason()))
                .statusHint(normalizeBlank(observation.getStatusHint()))
                .observedAt(observedAt)
                .operationalDate(operationalDate)
                .scanSequence(scanSequence)
                .imageCount(storedImages.size())
                .primaryImagePath(storedImages.get(0).filePath())
                .analysisStatus("PENDING_ANALYSIS")
                .finalState(null)
                .analysisNotes(null)
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
                .exactQrLabel(entity.getPlantQr())
                .groupKey(entity.getPlantGroupCode())
                .plantNumber(parsedQr.plantNumber())
                .potNumber(parsedQr.potNumber())
                .plantQr(entity.getPlantQr())
                .plantGroupCode(entity.getPlantGroupCode())
                .plantSide(entity.getPlantSide())
                .captureReason(entity.getCaptureReason())
                .statusHint(entity.getStatusHint())
                .operationalDate(entity.getOperationalDate())
                .scanSequence(entity.getScanSequence())
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
    @Transactional(readOnly = true)
    public List<RobotObservationResponseDto> getObservationsByPatrol(String patrolId) {
        List<RobotObservation> observations = robotObservationRepository.findByPatrolIdOrderByObservedAtAsc(patrolId);
        if (observations.isEmpty()) {
            return Collections.emptyList();
        }

        List<Long> observationIds = observations.stream()
                .map(RobotObservation::getId)
                .toList();

        Map<Long, List<RobotObservationImageResponseDto>> imagesByObservationId = new HashMap<>();
        for (RobotObservationImage image : robotObservationImageRepository.findByObservationIdInOrderByObservationIdAscSortOrderAsc(observationIds)) {
            Long observationId = image.getObservation().getId();
            imagesByObservationId.computeIfAbsent(observationId, ignored -> new ArrayList<>()).add(toImageResponse(image));
        }

        return observations.stream()
                .map(observation -> RobotObservationResponseDto.builder()
                        .id(observation.getId())
                        .robotId(observation.getRobotId())
                        .patrolId(observation.getPatrolId())
                        .exactQrLabel(observation.getPlantQr())
                        .groupKey(observation.getPlantGroupCode())
                        .plantNumber(parseQr(observation.getPlantQr()).plantNumber())
                        .potNumber(parseQr(observation.getPlantQr()).potNumber())
                        .plantQr(observation.getPlantQr())
                        .plantGroupCode(observation.getPlantGroupCode())
                        .plantSide(observation.getPlantSide())
                        .captureReason(observation.getCaptureReason())
                        .statusHint(observation.getStatusHint())
                        .operationalDate(observation.getOperationalDate())
                        .scanSequence(observation.getScanSequence())
                        .analysisStatus(observation.getAnalysisStatus())
                        .finalState(observation.getFinalState())
                        .analysisNotes(observation.getAnalysisNotes())
                        .observedAt(observation.getObservedAt())
                        .images(imagesByObservationId.getOrDefault(observation.getId(), List.of()))
                        .build())
                .toList();
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
        RobotStatus status = getOrCreateStatus();
        return buildPatrolAnalysis(patrolId, status.getRobotId(), false);
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
                        observation -> buildObservationAnalysisGroupKey(observation),
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
            RobotObservation representativeObservation = groupObservations.get(0);
            String publicGroupKey = normalizeToken(representativeObservation.getPlantGroupCode(), normalizeQr(representativeObservation.getPlantQr()));
            String finalState = resolveFinalState(groupObservations);
            String summary = buildPlantSummary(publicGroupKey, finalState, groupObservations.size());
            LocalDateTime lastObservedAt = groupObservations.get(groupObservations.size() - 1).getObservedAt();

            if (persistResults) {
                for (RobotObservation observation : groupObservations) {
                    observation.setAnalysisStatus("FINALIZED");
                    observation.setFinalState(finalState);
                    observation.setAnalysisNotes(summary);
                    robotObservationRepository.save(observation);
                }
                enqueuePlantStateUpdate(robotId, patrolId, publicGroupKey, representativeObservation.getPlantQr(), finalState, summary);
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
                    .groupKey(publicGroupKey)
                    .plantNumber(representativeObservation.getPlantQr() == null ? null : parseQr(representativeObservation.getPlantQr()).plantNumber())
                    .potNumber(representativeObservation.getPlantQr() == null ? null : parseQr(representativeObservation.getPlantQr()).potNumber())
                    .representativeExactQrLabel(representativeObservation.getPlantQr())
                    .plantGroupCode(publicGroupKey)
                    .representativePlantQr(representativeObservation.getPlantQr())
                    .operationalDate(representativeObservation.getOperationalDate())
                    .finalState(finalState)
                    .summary(summary)
                    .evidenceCount(groupObservations.size())
                    .lastObservedAt(lastObservedAt)
                    .sides(sides)
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

    private int resolveNextScanSequence(String patrolId, LocalDate operationalDate) {
        if (patrolId == null || patrolId.isBlank()) {
            return 1;
        }
        return (int) robotObservationRepository.countByPatrolIdAndOperationalDate(patrolId, operationalDate) + 1;
    }

    private String buildObservationAnalysisGroupKey(RobotObservation observation) {
        String groupKey = normalizeToken(observation.getPlantGroupCode(), normalizeQr(observation.getPlantQr()));
        if (observation.getOperationalDate() == null) {
            return groupKey;
        }
        return groupKey + "|" + observation.getOperationalDate();
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
            case SEARCH_BY_STATE -> "SEARCH_BY_STATE";
            case HEARTBEAT -> "HEARTBEAT";
        };
    }

    private Map<String, Object> resolveRobotCommandPayload(RobotCommandDto command) {
        Map<String, Object> payload = new LinkedHashMap<>();
        RobotCommandType commandType = command.getCommandType();
        SearchStartOrientation searchStartOrientation = resolveSearchStartOrientation(command.getSearchStartOrientation());
        if (commandType == RobotCommandType.MANUAL_MOVE) {
            payload.put("direction", command.getDirection() == null ? "stop" : command.getDirection().name().toLowerCase(Locale.ROOT));
            payload.put("speed", command.getSpeed() == null ? 0 : command.getSpeed());
        } else if (commandType == RobotCommandType.GOTO_PLANT) {
            String requestedTarget = normalizeQr(command.getTargetPlantQr());
            ParsedQr parsedQr = parseQr(requestedTarget);
            String groupKey = parsedQr.groupCode();
            payload.put("plantQr", requestedTarget);
            payload.put("groupKey", groupKey);
            payload.put("exactQrLabel", requestedTarget);
            payload.put("searchStartOrientation", searchStartOrientation.name());
            enrichTargetHistoryHint(payload, requestedTarget, groupKey);
        } else if (commandType == RobotCommandType.SWITCH_CAMERA) {
            payload.put("camera", normalizeBlank(command.getCameraName()));
        } else if (commandType == RobotCommandType.SET_SPEED_PROFILE) {
            payload.put("profile", normalizeToken(command.getSpeedProfile(), "MEDIUM"));
        } else if (commandType == RobotCommandType.RUN_ACRO) {
            payload.put("sequence", normalizeToken(command.getSequenceName(), "SPIN"));
        } else if (commandType == RobotCommandType.SEARCH_BY_STATE) {
            String requestedState = normalizeSearchState(command.getRequestedState());
            payload.put("state", requestedState);
            payload.put("searchStartOrientation", searchStartOrientation.name());
            payload.put("targets", resolveLatestTargetsForState(requestedState, searchStartOrientation));
        }
        return payload;
    }

    private void enrichTargetHistoryHint(Map<String, Object> payload, String requestedTarget, String groupKey) {
        if (requestedTarget == null || requestedTarget.isBlank()) {
            return;
        }
        RobotObservation latestObservation = isExactQrLabel(requestedTarget)
                ? robotObservationRepository.findTopByPlantQrOrderByObservedAtDesc(requestedTarget).orElse(null)
                : robotObservationRepository.findTopByPlantGroupCodeOrderByObservedAtDesc(groupKey).orElse(null);
        if (latestObservation == null) {
            return;
        }
        payload.put("historyPatrolId", latestObservation.getPatrolId());
        payload.put("expectedScanSequence", latestObservation.getScanSequence());
        payload.put("operationalDate", latestObservation.getOperationalDate() == null ? null : latestObservation.getOperationalDate().toString());
        payload.put("historyMatchedGroupKey", normalizeToken(latestObservation.getPlantGroupCode(), groupKey));
        payload.put("historyMatchedExactQrLabel", latestObservation.getPlantQr());

        if (latestObservation.getPatrolId() == null || latestObservation.getOperationalDate() == null) {
            return;
        }

        List<RobotObservation> patrolTimeline = robotObservationRepository.findByPatrolIdAndOperationalDateOrderByScanSequenceAsc(
                latestObservation.getPatrolId(),
                latestObservation.getOperationalDate()
        );
        payload.put("historySequenceCount", patrolTimeline.size());
        int observationIndex = -1;
        for (int index = 0; index < patrolTimeline.size(); index++) {
            if (Objects.equals(patrolTimeline.get(index).getId(), latestObservation.getId())) {
                observationIndex = index;
                break;
            }
        }
        if (observationIndex > 0) {
            RobotObservation previousObservation = patrolTimeline.get(observationIndex - 1);
            payload.put("neighborBeforeGroupKey", normalizeToken(previousObservation.getPlantGroupCode(), normalizeQr(previousObservation.getPlantQr())));
            payload.put("neighborBeforeExactQrLabel", previousObservation.getPlantQr());
            payload.put("neighborBeforeSequence", previousObservation.getScanSequence());
        }
        if (observationIndex >= 0 && observationIndex + 1 < patrolTimeline.size()) {
            RobotObservation nextObservation = patrolTimeline.get(observationIndex + 1);
            payload.put("neighborAfterGroupKey", normalizeToken(nextObservation.getPlantGroupCode(), normalizeQr(nextObservation.getPlantQr())));
            payload.put("neighborAfterExactQrLabel", nextObservation.getPlantQr());
            payload.put("neighborAfterSequence", nextObservation.getScanSequence());
        }
    }

    private List<Map<String, Object>> resolveLatestTargetsForState(String requestedState, SearchStartOrientation searchStartOrientation) {
        Map<String, RobotObservation> latestByGroupKey = new LinkedHashMap<>();
        for (RobotObservation observation : robotObservationRepository.findByFinalStateOrderByObservedAtDesc(requestedState)) {
            String groupKey = normalizeToken(observation.getPlantGroupCode(), normalizeQr(observation.getPlantQr()));
            latestByGroupKey.putIfAbsent(groupKey, observation);
        }

        return latestByGroupKey.values().stream()
                .sorted(Comparator.comparing(
                        RobotObservation::getScanSequence,
                        Comparator.nullsLast(Integer::compareTo)
                ))
                .map(observation -> {
                    Map<String, Object> target = new LinkedHashMap<>();
                    target.put("groupKey", normalizeToken(observation.getPlantGroupCode(), normalizeQr(observation.getPlantQr())));
                    target.put("exactQrLabel", observation.getPlantQr());
                    target.put("expectedScanSequence", observation.getScanSequence());
                    target.put("historySequenceCount", resolveHistorySequenceCount(observation));
                    target.put("searchStartOrientation", searchStartOrientation.name());
                    target.put("operationalDate", observation.getOperationalDate() == null ? null : observation.getOperationalDate().toString());
                    target.put("patrolId", observation.getPatrolId());
                    return target;
                })
                .toList();
    }

    private Integer resolveHistorySequenceCount(RobotObservation observation) {
        if (observation.getPatrolId() == null || observation.getOperationalDate() == null) {
            return null;
        }
        long count = robotObservationRepository.countByPatrolIdAndOperationalDate(
                observation.getPatrolId(),
                observation.getOperationalDate()
        );
        return count <= 0 ? null : (int) count;
    }

    private String normalizeSearchState(String rawState) {
        String normalized = normalizeToken(rawState, "ATENCION");
        return switch (normalized) {
            case "HEALTHY", "SANO" -> "SANO";
            case "ATTENTION", "ATENCION" -> "ATENCION";
            case "DANGER", "PELIGRO" -> "PELIGRO";
            case "UNKNOWN", "INCONCLUSA" -> "INCONCLUSA";
            default -> normalized;
        };
    }

    private boolean isExactQrLabel(String qrValue) {
        if (qrValue == null || qrValue.isBlank()) {
            return false;
        }
        String[] parts = qrValue.split("_");
        return parts.length >= 5 && ("IZ".equalsIgnoreCase(parts[4]) || "DR".equalsIgnoreCase(parts[4]));
    }

    private SearchStartOrientation resolveSearchStartOrientation(SearchStartOrientation orientation) {
        return orientation == null ? SearchStartOrientation.FORWARD : orientation;
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
        ParsedQr parsedQr = parseQr(plantGroupCode);
        String label = parsedQr.plantNumber() != null && parsedQr.potNumber() != null
                ? "Planta " + parsedQr.plantNumber() + " en maceta " + parsedQr.potNumber()
                : "Grupo " + plantGroupCode;
        return label
                + " consolidado en estado " + finalState
                + " con " + evidenceCount + " evidencias capturadas durante el patrullaje.";
    }

    private ParsedQr parseQr(String plantQr) {
        if (plantQr == null || plantQr.isBlank()) {
            return new ParsedQr("UNKNOWN", "NA", null, null);
        }
        String[] parts = plantQr.split("_");
        if (parts.length >= 5 && "PLA".equals(parts[0]) && "MA".equals(parts[2])) {
            String plantNumber = parts[1];
            String potNumber = parts[3];
            String groupCode = String.join("_", parts[0], plantNumber, parts[2], potNumber);
            String side = parts[4];
            return new ParsedQr(groupCode, side, plantNumber, potNumber);
        }
        return new ParsedQr(plantQr, "NA", null, null);
    }

    private record ParsedQr(String groupCode, String side, String plantNumber, String potNumber) {}
}
