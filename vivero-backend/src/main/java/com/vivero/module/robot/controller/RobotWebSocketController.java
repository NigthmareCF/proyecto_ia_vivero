package com.vivero.module.robot.controller;

import com.vivero.module.robot.dto.ManualControlDto;
import com.vivero.module.robot.dto.RobotStatusResponseDto;
import com.vivero.module.robot.service.RobotService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

/**
 * Controlador WebSocket para control manual y relay de stream.
 */
@Controller
@RequiredArgsConstructor
public class RobotWebSocketController {

    private final RobotService robotService;
    private final SimpMessagingTemplate messagingTemplate;

    @MessageMapping("/robot/control")
    public void handleManualControl(@Valid ManualControlDto control) {
        RobotStatusResponseDto status = robotService.applyManualControl(control);
        messagingTemplate.convertAndSend("/topic/robot/control", status);
    }

    @MessageMapping("/robot/stream")
    public void relayCameraStream(String payload) {
        messagingTemplate.convertAndSend("/topic/robot/stream", payload);
    }
}