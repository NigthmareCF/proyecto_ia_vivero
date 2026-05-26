package com.vivero.module.analisis.service;

import com.vivero.module.analisis.dto.PlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisResponseDto;
import com.vivero.module.analisis.dto.ManualPlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisHistoryItemDto;

import java.util.List;

public interface PlantAnalysisService {

    PlantAnalysisResponseDto analyzePlant(PlantAnalysisRequestDto request, String currentUserEmail);

    PlantAnalysisHistoryItemDto createManualAnalysis(ManualPlantAnalysisRequestDto request, String currentUserEmail);

    List<PlantAnalysisHistoryItemDto> getAnalysisHistory();

    StoredAnalysisImage getAnalysisImage(Long imageId);

    record StoredAnalysisImage(String mimeType, byte[] content) {
    }
}
