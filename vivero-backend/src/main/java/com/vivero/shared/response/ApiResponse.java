package com.vivero.shared.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * Envuelve todas las respuestas REST del sistema.
 * Garantiza un formato consistente tanto en éxito como en error.
 *
 * Ejemplo de éxito:
 * {
 *   "success": true,
 *   "message": "Plant found",
 *   "data": { ... },
 *   "timestamp": "2026-03-18T14:30:00"
 * }
 *
 * Ejemplo de error:
 * {
 *   "success": false,
 *   "message": "Plant not found",
 *   "error": "PLANT_NOT_FOUND",
 *   "timestamp": "2026-03-18T14:30:00"
 * }
 */
@Getter
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {

    private final boolean success;
    private final String message;
    private final T data;
    private final String error;

    @Builder.Default
    private final LocalDateTime timestamp = LocalDateTime.now();

    // Métodos de fábrica para uso rápido desde controllers.

    public static <T> ApiResponse<T> ok(String message, T data) {
        return ApiResponse.<T>builder()
                .success(true)
                .message(message)
                .data(data)
                .build();
    }

    public static <T> ApiResponse<T> ok(T data) {
        return ok("OK", data);
    }

    public static <T> ApiResponse<T> error(String message, String errorCode) {
        return ApiResponse.<T>builder()
                .success(false)
                .message(message)
                .error(errorCode)
                .build();
    }
}
