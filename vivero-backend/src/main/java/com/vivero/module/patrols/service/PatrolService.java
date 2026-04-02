package com.vivero.module.patrols.service;

import com.vivero.module.patrols.dto.PatrolResponseDto;
import com.vivero.module.patrols.dto.PatrolResultRequestDto;
import com.vivero.module.patrols.dto.StartPatrolRequestDto;
import com.vivero.shared.enums.PatrolStatus;

import java.util.List;

/**
 * Contrato del módulo patrols.
 */
public interface PatrolService {

    List<PatrolResponseDto> getAllPatrols(PatrolStatus status);

    PatrolResponseDto getPatrolById(Long id);

    PatrolResponseDto startPatrol(StartPatrolRequestDto request, String currentUserEmail);

    PatrolResponseDto registerResult(Long patrolId, PatrolResultRequestDto request);

    PatrolResponseDto completePatrol(Long patrolId);
}