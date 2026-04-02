package com.vivero.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * Configura el broker de mensajes WebSocket con protocolo STOMP.
 *
 * Flujos principales que usa este WebSocket:
 *
 * 1. Control manual del robot (frontend → backend → robot)
 *    Frontend publica en: /app/robot/control
 *    Backend reenvía al robot bridge
 *
 * 2. Stream de cámara en tiempo real (robot → backend → frontend)
 *    Backend publica en: /topic/robot/stream
 *    Frontend se suscribe a ese topic
 *
 * 3. Actualizaciones de estado de plantas durante patrullaje
 *    Backend publica en: /topic/patrol/updates
 *    Frontend se suscribe para actualizar el dashboard en tiempo real
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(@NonNull MessageBrokerRegistry registry) {
        // Prefijo para topics a los que se suscriben los clientes (frontend)
        registry.enableSimpleBroker("/topic", "/queue");

        // Prefijo para mensajes que envía el cliente al servidor
        registry.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(@NonNull StompEndpointRegistry registry) {
        // Endpoint de conexión WebSocket, el frontend conecta aquí
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")  // ajustar en producción con dominio real
                .withSockJS();                  // fallback para navegadores sin WS nativo
    }
}