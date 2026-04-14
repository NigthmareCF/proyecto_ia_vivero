package com.vivero.module.analisis.controller;

import com.vivero.module.analisis.dto.PlantAnalysisRequest;
import com.vivero.module.analisis.dto.PlantAnalysisResponse;
import com.vivero.module.analisis.service.PlantAnalysisService;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/analisis")
@RequiredArgsConstructor
public class PlantAnalysisController {

    private final PlantAnalysisService plantAnalysisService;

    @PostMapping("/planta")
    public ResponseEntity<ApiResponse<PlantAnalysisResponse>> analyzePlant(
            @Valid @RequestBody PlantAnalysisRequest request
    ) {
        PlantAnalysisResponse response = plantAnalysisService.analyzePlant(request);
        return ResponseEntity.ok(ApiResponse.ok("Analisis generado correctamente", response));
    }
}
