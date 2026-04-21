package com.vivero.module.robot.entity;

import com.vivero.shared.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Imagen individual asociada a una observación del robot.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "robot_observation_images")
public class RobotObservationImage extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "observation_id", nullable = false)
    private RobotObservation observation;

    @Column(name = "file_path", nullable = false, length = 255)
    private String filePath;

    @Column(name = "mime_type", nullable = false, length = 80)
    private String mimeType;

    @Column(name = "sort_order", nullable = false)
    private Integer sortOrder;

    @Column(name = "is_relevant", nullable = false)
    @Builder.Default
    private boolean relevant = false;
}
