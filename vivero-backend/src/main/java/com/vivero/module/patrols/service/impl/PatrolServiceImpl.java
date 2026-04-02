package com.vivero.module.patrols.service.impl;

import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.patrols.dto.PatrolResponseDto;
import com.vivero.module.patrols.dto.PatrolResultRequestDto;
import com.vivero.module.patrols.dto.StartPatrolRequestDto;
import com.vivero.module.patrols.entity.Observation;
import com.vivero.module.patrols.entity.Patrol;
import com.vivero.module.patrols.mapper.PatrolMapper;
import com.vivero.module.patrols.repository.ObservationRepository;
import com.vivero.module.patrols.repository.PatrolRepository;
import com.vivero.module.patrols.service.PatrolService;
import com.vivero.shared.enums.PatrolStatus;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Objects;

/**
 * Implementación del módulo patrols.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PatrolServiceImpl implements PatrolService {

    private final PatrolRepository patrolRepository;
    private final ObservationRepository observationRepository;
    private final UserRepository userRepository;
    private final PatrolMapper patrolMapper;

    @Override
    @Transactional(readOnly = true)
    public List<PatrolResponseDto> getAllPatrols(PatrolStatus status) {
        List<Patrol> patrols = status != null
                ? patrolRepository.findByStatus(status)
                : patrolRepository.findAll(Sort.by(Sort.Direction.DESC, "startedAt"));

        return patrols.stream()
                .map(patrolMapper::toResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public PatrolResponseDto getPatrolById(Long id) {
        return patrolMapper.toResponse(findPatrolOrThrow(id));
    }

    @Override
    @Transactional
    public PatrolResponseDto startPatrol(StartPatrolRequestDto request, String currentUserEmail) {
        User user = findUserOrThrow(currentUserEmail);

        Patrol patrol = Objects.requireNonNull(
                Patrol.builder()
                        .startedBy(user)
                        .mode(request.getMode())
                        .filter(request.getFilter())
                        .status(PatrolStatus.IN_PROGRESS)
                        .startedAt(LocalDateTime.now())
                        .build()
        );

        patrolRepository.save(patrol);
        log.info("Patrullaje iniciado por {} con modo {} y filtro {}", user.getEmail(), patrol.getMode(), patrol.getFilter());
        return patrolMapper.toResponse(patrol);
    }

    @Override
    @Transactional
    public PatrolResponseDto registerResult(Long patrolId, PatrolResultRequestDto request) {
        Patrol patrol = findPatrolOrThrow(patrolId);
        validatePatrolInProgress(patrol);

        Observation observation = Objects.requireNonNull(
                Observation.builder()
                        .patrol(patrol)
                        .plantQrCode(request.getPlantQrCode().trim().toUpperCase())
                        .aiResult(request.getAiResult())
                        .aiConfidence(request.getAiConfidence())
                        .manualCauses(normalizeText(request.getManualCauses()))
                        .operatorNotes(normalizeText(request.getOperatorNotes()))
                        .imagePaths(normalizeText(request.getImagePaths()))
                        .timestamp(LocalDateTime.now())
                        .build()
        );

        observationRepository.save(observation);
        patrol.getObservations().add(observation);

        log.info("Resultado registrado para patrullaje {} en planta {}", patrol.getId(), observation.getPlantQrCode());
        return patrolMapper.toResponse(patrol);
    }

    @Override
    @Transactional
    public PatrolResponseDto completePatrol(Long patrolId) {
        Patrol patrol = findPatrolOrThrow(patrolId);
        validatePatrolInProgress(patrol);

        patrol.setStatus(PatrolStatus.COMPLETED);
        patrol.setCompletedAt(LocalDateTime.now());

        log.info("Patrullaje completado: {}", patrol.getId());
        return patrolMapper.toResponse(patrol);
    }

    private void validatePatrolInProgress(Patrol patrol) {
        if (patrol.getStatus() != PatrolStatus.IN_PROGRESS) {
            throw new BusinessException(
                    "Patrol is not in progress",
                    "PATROL_NOT_IN_PROGRESS"
            );
        }
    }

    private @NonNull Patrol findPatrolOrThrow(@NonNull Long id) {
        return patrolRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Patrol not found with id: " + id));
    }

    private @NonNull User findUserOrThrow(@NonNull String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));
    }

    private String normalizeText(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }
}