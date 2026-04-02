package com.vivero.module.patrols.entity;

import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.PlantState;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Observación individual registrada durante un patrullaje.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "observations")
public class Observation extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "patrol_id", nullable = false)
    private Patrol patrol;

    @Column(name = "plant_qr_code", nullable = false, length = 120)
    private String plantQrCode;

    @Enumerated(EnumType.STRING)
    @Column(name = "ai_result", nullable = false, length = 20)
    private PlantState aiResult;

    @Column(name = "ai_confidence", nullable = false)
    private Double aiConfidence;

    @Column(name = "manual_causes", length = 255)
    private String manualCauses;

    @Column(name = "operator_notes", length = 500)
    private String operatorNotes;

    @Column(name = "image_paths", length = 2000)
    private String imagePaths;

    @Column(nullable = false)
    private LocalDateTime timestamp;
}