package com.vivero.shared.exception;

/**
 * Thrown when a requested resource does not exist in the database.
 * Results in HTTP 404.
 *
 * Usage: throw new ResourceNotFoundException("Plant with QR " + qrCode + " not found");
 */
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
