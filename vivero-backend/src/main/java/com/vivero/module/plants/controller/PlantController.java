package com.vivero.module.plants.controller;

import com.vivero.module.plants.dto.PlantRequestDto;
import com.vivero.module.plants.dto.PlantResponseDto;
import com.vivero.module.plants.service.PlantService;
import com.vivero.shared.enums.PlantState;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * API REST del módulo plants.
 */
@RestController
@RequestMapping("/plants")
@RequiredArgsConstructor
public class PlantController {

    private final PlantService plantService;

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<PlantResponseDto>>> getAllPlants() {
        return ResponseEntity.ok(ApiResponse.ok("Plants retrieved successfully", plantService.getAllPlants()));
    }

    @GetMapping("/{qrCode}")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR', 'VIEWER')")
    public ResponseEntity<ApiResponse<PlantResponseDto>> getPlantByQrCode(@PathVariable String qrCode) {
        return ResponseEntity.ok(ApiResponse.ok("Plant retrieved successfully", plantService.getPlantByQrCode(qrCode)));
    }

    @GetMapping("/state/{state}")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<PlantResponseDto>>> getPlantsByState(@PathVariable PlantState state) {
        return ResponseEntity.ok(ApiResponse.ok("Plants filtered successfully", plantService.getPlantsByState(state)));
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<ApiResponse<PlantResponseDto>> createPlant(@Valid @RequestBody PlantRequestDto request) {
        PlantResponseDto response = plantService.createPlant(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Plant created successfully", response));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<ApiResponse<PlantResponseDto>> updatePlant(
            @PathVariable Long id,
            @Valid @RequestBody PlantRequestDto request) {

        return ResponseEntity.ok(ApiResponse.ok("Plant updated successfully", plantService.updatePlant(id, request)));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<ApiResponse<Void>> deletePlant(@PathVariable Long id) {
        plantService.deletePlant(id);
        return ResponseEntity.ok(ApiResponse.ok("Plant deleted successfully", null));
    }
}