package com.vivero.module.robot.controller;

import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.service.RobotService;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * API REST del módulo robot.
 */
@RestController
@RequestMapping("/robot")
@RequiredArgsConstructor
public class RobotController {

    private final RobotService robotService;

    @PostMapping("/command")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR')")
    public ResponseEntity<ApiResponse<RobotStatusResponseDto>> sendCommand(@Valid @RequestBody RobotCommandDto command) {
        return ResponseEntity.ok(ApiResponse.ok("Robot command processed successfully", robotService.sendCommand(command)));
    }

    @GetMapping("/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'OPERATOR', 'VIEWER')")
    public ResponseEntity<ApiResponse<RobotStatusResponseDto>> getStatus() {
        return ResponseEntity.ok(ApiResponse.ok("Robot status retrieved successfully", robotService.getCurrentStatus()));
    }
}