package com.vivero.shared.exception;

import lombok.Getter;

/**
 * Thrown for business logic errors.
 * Results in HTTP 400.
 *
 * Usage: throw new BusinessException("Robot is already in motion", "ROBOT_BUSY");
 */
@Getter
public class BusinessException extends RuntimeException {

    private final String code;

    public BusinessException(String message, String code) {
        super(message);
        this.code = code;
    }

    public BusinessException(String message, String code, Throwable cause) {
        super(message, cause);
        this.code = code;
    }
}
