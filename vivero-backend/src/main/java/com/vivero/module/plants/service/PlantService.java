package com.vivero.module.plants.service;

import com.vivero.module.plants.dto.PlantRequestDto;
import com.vivero.module.plants.dto.PlantResponseDto;
import com.vivero.shared.enums.PlantState;

import java.util.List;

/**
 * Contrato del módulo plants.
 */
public interface PlantService {

    List<PlantResponseDto> getAllPlants();

    PlantResponseDto getPlantByQrCode(String qrCode);

    List<PlantResponseDto> getPlantsByState(PlantState state);

    PlantResponseDto createPlant(PlantRequestDto request);

    PlantResponseDto updatePlant(Long id, PlantRequestDto request);

    void deletePlant(Long id);
}