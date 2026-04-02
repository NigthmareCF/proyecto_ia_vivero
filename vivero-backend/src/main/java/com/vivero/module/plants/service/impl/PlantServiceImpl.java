package com.vivero.module.plants.service.impl;

import com.vivero.module.plants.dto.PlantRequestDto;
import com.vivero.module.plants.dto.PlantResponseDto;
import com.vivero.module.plants.entity.Plant;
import com.vivero.module.plants.mapper.PlantMapper;
import com.vivero.module.plants.repository.PlantRepository;
import com.vivero.module.plants.service.PlantService;
import com.vivero.shared.enums.PlantState;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;

/**
 * Implementación del módulo plants.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PlantServiceImpl implements PlantService {

    private final PlantRepository plantRepository;
    private final PlantMapper plantMapper;

    @Override
    @Transactional(readOnly = true)
    public List<PlantResponseDto> getAllPlants() {
        return plantRepository.findAll(Sort.by(Sort.Direction.ASC, "name")).stream()
                .map(plantMapper::toResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public PlantResponseDto getPlantByQrCode(String qrCode) {
        return plantMapper.toResponse(findByQrCodeOrThrow(qrCode));
    }

    @Override
    @Transactional(readOnly = true)
    public List<PlantResponseDto> getPlantsByState(PlantState state) {
        return plantRepository.findByCurrentState(state).stream()
                .map(plantMapper::toResponse)
                .toList();
    }

    @Override
    @Transactional
    public PlantResponseDto createPlant(PlantRequestDto request) {
        String normalizedQrCode = normalizeQrCode(request.getQrCode());

        if (plantRepository.existsByQrCode(normalizedQrCode)) {
            throw new BusinessException(
                    "QR code already registered: " + normalizedQrCode,
                    "PLANT_QR_ALREADY_EXISTS"
            );
        }

        Plant plant = Objects.requireNonNull(
                Plant.builder()
                        .qrCode(normalizedQrCode)
                        .name(request.getName().trim())
                        .location(request.getLocation().trim())
                        .description(normalizeDescription(request.getDescription()))
                        .currentState(request.getCurrentState())
                        .build()
        );

        plantRepository.save(plant);
        log.info("Planta registrada: {} ({})", plant.getName(), plant.getQrCode());
        return plantMapper.toResponse(plant);
    }

    @Override
    @Transactional
    public PlantResponseDto updatePlant(Long id, PlantRequestDto request) {
        Plant plant = findByIdOrThrow(id);
        String normalizedQrCode = normalizeQrCode(request.getQrCode());

        if (plantRepository.existsByQrCodeAndIdNot(normalizedQrCode, id)) {
            throw new BusinessException(
                    "QR code already registered: " + normalizedQrCode,
                    "PLANT_QR_ALREADY_EXISTS"
            );
        }

        plant.setQrCode(normalizedQrCode);
        plant.setName(request.getName().trim());
        plant.setLocation(request.getLocation().trim());
        plant.setDescription(normalizeDescription(request.getDescription()));
        plant.setCurrentState(request.getCurrentState());

        log.info("Planta actualizada: {} ({})", plant.getName(), plant.getQrCode());
        return plantMapper.toResponse(plant);
    }

    @Override
    @Transactional
    public void deletePlant(Long id) {
        Plant plant = findByIdOrThrow(id);
        plantRepository.delete(plant);
        log.info("Planta eliminada: {} ({})", plant.getName(), plant.getQrCode());
    }

    private @NonNull Plant findByIdOrThrow(@NonNull Long id) {
        return plantRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Plant not found with id: " + id));
    }

    private @NonNull Plant findByQrCodeOrThrow(@NonNull String qrCode) {
        String normalizedQrCode = normalizeQrCode(qrCode);
        return plantRepository.findByQrCode(normalizedQrCode)
                .orElseThrow(() -> new ResourceNotFoundException("Plant not found with QR code: " + normalizedQrCode));
    }

    private String normalizeQrCode(String qrCode) {
        return qrCode.trim().toUpperCase();
    }

    private String normalizeDescription(String description) {
        if (description == null || description.trim().isEmpty()) {
            return null;
        }
        return description.trim();
    }
}