package com.vivero.module.robot.websocket;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.net.URI;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Slf4j
@Component
@RequiredArgsConstructor
public class RobotStreamWebSocketHandler extends TextWebSocketHandler {

    private final SimpMessagingTemplate messagingTemplate;
    private final Set<WebSocketSession> viewerSessions = ConcurrentHashMap.newKeySet();
    private final AtomicLong relayedFrameCount = new AtomicLong();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        boolean producer = isRobotProducer(session);
        if (!producer) {
            viewerSessions.add(session);
        }
        log.info(
                "Robot stream websocket connected: {} role={} viewers={} uri={}",
                session.getId(),
                producer ? "robot-producer" : "viewer",
                viewerSessions.size(),
                session.getUri()
        );
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        if (!isRobotProducer(session)) {
            return;
        }
        messagingTemplate.convertAndSend("/topic/robot/stream", message.getPayload());
        long frameCount = relayedFrameCount.incrementAndGet();
        for (WebSocketSession viewer : viewerSessions) {
            if (viewer.isOpen()) {
                viewer.sendMessage(message);
            }
        }
        if (frameCount == 1 || frameCount % 30 == 0) {
            log.info("Robot stream frame relayed: count={} viewers={} bytes={}", frameCount, viewerSessions.size(), message.getPayloadLength());
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        viewerSessions.remove(session);
        log.info("Robot stream websocket closed: {} - {} viewers={}", session.getId(), status, viewerSessions.size());
    }

    private boolean isRobotProducer(WebSocketSession session) {
        URI uri = session.getUri();
        if (uri == null || uri.getQuery() == null) {
            return false;
        }
        String query = uri.getQuery().toLowerCase();
        return query.contains("role=robot") || query.contains("source=robot");
    }
}
