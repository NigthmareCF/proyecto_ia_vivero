package com.vivero;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Application entry point — Autonomous Greenhouse Monitoring System.
 *
 * @EnableAsync       — notifications (email, WhatsApp, Telegram) run on
 *                      separate threads to avoid blocking REST responses
 * @EnableScheduling  — scheduled tasks for automatic reports and alerts
 * @EnableJpaAuditing — activates @CreatedDate / @LastModifiedDate on BaseEntity
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
