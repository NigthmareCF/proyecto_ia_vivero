package com.vivero.module.robot.entity;

import com.vivero.shared.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Evidencia capturada por la Raspberry Pi para una planta o punto del recorrido.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "robot_observations")
public class RobotObservation extends BaseEntity {

    @Column(name = "robot_id", nullable = false, length = 80)
    private String robotId;

    @Column(name = "patrol_id", length = 80)
    private String patrolId;

    @Column(name = "plant_qr", nullable = false, length = 120)
    private String plantQr;

    @Column(name = "plant_group_code", length = 120)
    private String plantGroupCode;

    @Column(name = "plant_side", length = 20)
    private String plantSide;

    @Column(name = "capture_reason", length = 80)
    private String captureReason;

    @Column(name = "status_hint", length = 80)
    private String statusHint;

    @Column(name = "observed_at", nullable = false)
    private LocalDateTime observedAt;

    @Column(name = "image_count", nullable = false)
    private Integer imageCount;

    @Column(name = "primary_image_path", length = 255)
    private String primaryImagePath;

    @Column(name = "analysis_status", nullable = false, length = 40)
    private String analysisStatus;

    @Column(name = "final_state", length = 40)
    private String finalState;

    @Column(name = "analysis_notes", length = 1000)
    private String analysisNotes;
}
