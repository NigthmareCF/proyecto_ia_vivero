package com.vivero.module.robot.controller;

import com.vivero.module.robot.dto.RobotCommandAckRequestDto;
import com.vivero.module.robot.dto.RobotCommandDto;
import com.vivero.module.robot.dto.RobotHeartbeatRequestDto;
import com.vivero.module.robot.dto.RobotObservationRequestDto;
import com.vivero.module.robot.dto.RobotObservationResponseDto;
import com.vivero.module.robot.dto.RobotPatrolAnalysisResponseDto;
import com.vivero.module.robot.dto.RobotQueuedCommandResponseDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.service.RobotService;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/robot")
@RequiredArgsConstructor
public class RobotController {

    private final RobotService robotService;

    @PostMapping("/command")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER')")
    public ResponseEntity<ApiResponse<RobotStatusResponseDto>> sendCommand(@Valid @RequestBody RobotCommandDto command) {
        return ResponseEntity.ok(ApiResponse.ok("Robot command processed successfully", robotService.sendCommand(command)));
    }

    @PostMapping("/heartbeat")
    public ResponseEntity<ApiResponse<RobotStatusResponseDto>> processHeartbeat(@Valid @RequestBody RobotHeartbeatRequestDto heartbeat) {
        return ResponseEntity.ok(ApiResponse.ok("Robot heartbeat processed successfully", robotService.processHeartbeat(heartbeat)));
    }

    @PostMapping("/observations")
    public ResponseEntity<ApiResponse<RobotObservationResponseDto>> registerObservation(@Valid @RequestBody RobotObservationRequestDto observation) {
        return ResponseEntity.ok(ApiResponse.ok("Robot observation stored successfully", robotService.registerObservation(observation)));
    }

    @PostMapping("/patrols/{patrolId}/analysis/finalize")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER')")
    public ResponseEntity<ApiResponse<RobotPatrolAnalysisResponseDto>> finalizePatrolAnalysis(
            @PathVariable String patrolId,
            @RequestParam(required = false, defaultValue = "ROBOT-001") String robotId
    ) {
        return ResponseEntity.ok(ApiResponse.ok(
                "Robot patrol analysis finalized successfully",
                robotService.finalizePatrolAnalysis(patrolId, robotId)
        ));
    }

    @GetMapping("/patrols/{patrolId}/analysis")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<RobotPatrolAnalysisResponseDto>> getPatrolAnalysis(@PathVariable String patrolId) {
        return ResponseEntity.ok(ApiResponse.ok(
                "Robot patrol analysis retrieved successfully",
                robotService.getPatrolAnalysis(patrolId)
        ));
    }

    @GetMapping("/commands/next")
    public ResponseEntity<ApiResponse<RobotQueuedCommandResponseDto>> pollNextCommand(@RequestParam String robotId) {
        RobotQueuedCommandResponseDto command = robotService.pollNextCommand(robotId);
        if (command == null) {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
        }
        return ResponseEntity.ok(ApiResponse.ok("Robot command retrieved successfully", command));
    }

    @PostMapping("/commands/{commandId}/ack")
    public ResponseEntity<ApiResponse<String>> acknowledgeCommand(
            @PathVariable Long commandId,
            @Valid @RequestBody RobotCommandAckRequestDto request
    ) {
        robotService.acknowledgeCommand(commandId, request);
        return ResponseEntity.ok(ApiResponse.ok("Robot command acknowledged", "ACK"));
    }

    @GetMapping("/status")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<ApiResponse<RobotStatusResponseDto>> getStatus() {
        return ResponseEntity.ok(ApiResponse.ok("Robot status retrieved successfully", robotService.getCurrentStatus()));
    }

    @GetMapping("/observations/images/{imageId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'CONTROLLER', 'VIEWER')")
    public ResponseEntity<Resource> getObservationImage(@PathVariable Long imageId) {
        Resource image = robotService.loadObservationImage(imageId);
        return ResponseEntity.ok()
                .header(HttpHeaders.CACHE_CONTROL, "no-cache")
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .body(image);
    }
}
