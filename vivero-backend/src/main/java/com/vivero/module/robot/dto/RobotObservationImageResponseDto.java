package com.vivero.module.robot.dto;

import lombok.Builder;
import lombok.Getter;

/**
 * Imagen almacenada para una observación del robot.
 */
@Getter
@Builder
public class RobotObservationImageResponseDto {

    private Long id;
    private String mimeType;
    private Integer sortOrder;
    private boolean relevant;
    private String imageUrl;
}
