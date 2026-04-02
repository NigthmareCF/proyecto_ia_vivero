package com.vivero.module.patrols.controller;

import com.vivero.module.patrols.dto.PatrolResponseDto;
import com.vivero.module.patrols.dto.PatrolResultRequestDto;
import com.vivero.module.patrols.dto.StartPatrolRequestDto;
import com.vivero.module.patrols.service.PatrolService;
import com.vivero.shared.enums.PatrolStatus;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * API REST del módulo patrols.
 */
@RestController
@RequestMapping("/patrols")
@RequiredArgsConstructor
public class PatrolController {

    private final PatrolService patrolService;

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR', 'VIEWER')")
    public ResponseEntity<ApiResponse<List<PatrolResponseDto>>> getAllPatrols(
            @RequestParam(required = false) PatrolStatus status) {

        return ResponseEntity.ok(ApiResponse.ok("Patrols retrieved successfully", patrolService.getAllPatrols(status)));
    }

    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR', 'VIEWER')")
    public ResponseEntity<ApiResponse<PatrolResponseDto>> getPatrolById(@PathVariable Long id) {
        return ResponseEntity.ok(ApiResponse.ok("Patrol retrieved successfully", patrolService.getPatrolById(id)));
    }

    @PostMapping("/start")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<ApiResponse<PatrolResponseDto>> startPatrol(
            @Valid @RequestBody StartPatrolRequestDto request,
            Authentication authentication) {

        PatrolResponseDto response = patrolService.startPatrol(request, authentication.getName());
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Patrol started successfully", response));
    }

    @PostMapping("/{id}/result")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<ApiResponse<PatrolResponseDto>> registerResult(
            @PathVariable Long id,
            @Valid @RequestBody PatrolResultRequestDto request) {

        return ResponseEntity.ok(ApiResponse.ok("Patrol result registered successfully", patrolService.registerResult(id, request)));
    }

    @PostMapping("/{id}/complete")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<ApiResponse<PatrolResponseDto>> completePatrol(@PathVariable Long id) {
        return ResponseEntity.ok(ApiResponse.ok("Patrol completed successfully", patrolService.completePatrol(id)));
    }
}