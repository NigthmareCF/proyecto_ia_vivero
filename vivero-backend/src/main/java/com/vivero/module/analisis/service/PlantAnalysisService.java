package com.vivero.module.analisis.service;

import com.vivero.module.analisis.dto.PlantAnalysisRequest;
import com.vivero.module.analisis.dto.PlantAnalysisResponse;

public interface PlantAnalysisService {

    PlantAnalysisResponse analyzePlant(PlantAnalysisRequest request);
}
