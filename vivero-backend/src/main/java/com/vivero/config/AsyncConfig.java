package com.vivero.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * Configura el pool de hilos para tareas asíncronas (@Async).
 *
 * Las notificaciones (email, WhatsApp y SMS) se ejecutan en este pool
 * para no bloquear el hilo principal de la petición REST.
 * Si el envío de un email tarda 3 segundos, el usuario no espera esos 3 segundos.
 */
@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "notificationExecutor")
    public Executor notificationExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();

        // Hilos base siempre activos esperando tareas
        executor.setCorePoolSize(4);

        // Máximo de hilos en momentos de alta carga (muchas notificaciones simultáneas)
        executor.setMaxPoolSize(10);

        // Cola de tareas pendientes si todos los hilos están ocupados
        executor.setQueueCapacity(50);

        // Prefijo para identificar estos hilos en los logs
        executor.setThreadNamePrefix("notification-");

        executor.initialize();
        return executor;
    }
}
