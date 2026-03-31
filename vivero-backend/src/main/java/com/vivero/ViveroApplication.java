package com.vivero;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Punto de entrada principal de la aplicación.
 *
 * @EnableAsync       ejecuta tareas asíncronas como notificaciones sin bloquear
 *                    la respuesta HTTP principal.
 * @EnableScheduling  habilita tareas programadas para reportes y alertas futuras.
 * @EnableJpaAuditing activa @CreatedDate y @LastModifiedDate en BaseEntity.
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
@EnableJpaAuditing
public class ViveroApplication {

    public static void main(String[] args) {
        SpringApplication.run(ViveroApplication.class, args);
    }
}
