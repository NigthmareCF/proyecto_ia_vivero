package com.vivero.module.robot.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Observación capturada por la Raspberry Pi y enviada al backend.
 */
@Getter
@Setter
public class RobotObservationRequestDto {

    @NotBlank(message = "Robot id is required")
    @Size(max = 80, message = "Robot id must not exceed 80 characters")
    private String robotId;

    @Size(max = 80, message = "Patrol id must not exceed 80 characters")
    private String patrolId;

    @NotBlank(message = "Plant QR is required")
    @Size(max = 120, message = "Plant QR must not exceed 120 characters")
    private String plantQr;

    @Size(max = 80, message = "Capture reason must not exceed 80 characters")
    private String captureReason;

    @Size(max = 80, message = "Status hint must not exceed 80 characters")
    private String statusHint;

    private LocalDateTime observedAt;

    @Size(max = 80, message = "Mime type must not exceed 80 characters")
    private String mimeType;

    @NotEmpty(message = "At least one image is required")
    private List<String> imagesBase64;
}
