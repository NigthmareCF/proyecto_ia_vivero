package com.vivero.module.analisis.controller;

import com.vivero.module.analisis.dto.ManualPlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisHistoryItemDto;
import com.vivero.module.analisis.dto.PlantAnalysisRequestDto;
import com.vivero.module.analisis.dto.PlantAnalysisResponseDto;
import com.vivero.module.analisis.service.PlantAnalysisService;
import com.vivero.module.auth.entity.User;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/analisis")
@RequiredArgsConstructor
public class PlantAnalysisController {

    private final PlantAnalysisService plantAnalysisService;

    @PostMapping("/planta")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<PlantAnalysisResponseDto>> analyzePlant(
            @Valid @RequestBody PlantAnalysisRequestDto request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        PlantAnalysisResponseDto response = plantAnalysisService.analyzePlant(request, user.getEmail());
        return ResponseEntity.ok(ApiResponse.ok("Analisis de planta generado correctamente", response));
    }

    @PostMapping("/manual")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<PlantAnalysisHistoryItemDto>> createManualAnalysis(
            @Valid @RequestBody ManualPlantAnalysisRequestDto request,
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        PlantAnalysisHistoryItemDto response = plantAnalysisService.createManualAnalysis(request, user.getEmail());
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Analisis manual guardado correctamente", response));
    }

    @GetMapping("/history")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<PlantAnalysisHistoryItemDto>>> getAnalysisHistory() {
        return ResponseEntity.ok(ApiResponse.ok("Historial de analisis recuperado", plantAnalysisService.getAnalysisHistory()));
    }

    @GetMapping("/images/{imageId}")
    public ResponseEntity<byte[]> getAnalysisImage(@PathVariable Long imageId) {
        PlantAnalysisService.StoredAnalysisImage image = plantAnalysisService.getAnalysisImage(imageId);
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(image.mimeType()));
        return ResponseEntity.ok().headers(headers).body(image.content());
    }
}
