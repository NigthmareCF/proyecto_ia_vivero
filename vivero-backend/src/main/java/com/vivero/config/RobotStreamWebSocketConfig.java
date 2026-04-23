package com.vivero.config;

import com.vivero.module.robot.websocket.RobotStreamWebSocketHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
@RequiredArgsConstructor
public class RobotStreamWebSocketConfig implements WebSocketConfigurer {

    private final RobotStreamWebSocketHandler robotStreamWebSocketHandler;

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(robotStreamWebSocketHandler, "/ws/robot-stream")
                .setAllowedOriginPatterns("*");
    }
}
