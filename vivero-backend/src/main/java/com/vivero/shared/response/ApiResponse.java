package com.vivero.shared.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

/**
 * Wraps ALL REST responses in the system.
 * Guarantees a consistent format for both success and error cases.
 *
 * Success example:
 * {
 *   "success": true,
 *   "message": "Plant found",
 *   "data": { ... },
 *   "timestamp": "2026-03-18T14:30:00"
 * }
 *
 * Error example:
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

    // -- Factory methods for quick use in controllers --

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
