package com.vivero.module.reports.entity;

import com.vivero.module.auth.entity.User;
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
 * Entidad principal del módulo de reportes.
 * Mantiene una referencia desacoplada al patrullaje mediante su ID para no depender todavía del módulo patrols.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "reports")
public class Report extends BaseEntity {

    @Column(name = "patrol_id")
    private Long patrolId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "generated_by", nullable = false)
    private User generatedBy;

    @Column(nullable = false, length = 150)
    private String title;

    @Column(length = 1000)
    private String summary;

    @Column(name = "observations_count", nullable = false)
    private Integer observationsCount;

    @Column(name = "healthy_count", nullable = false)
    private Integer healthyCount;

    @Column(name = "attention_count", nullable = false)
    private Integer attentionCount;

    @Column(name = "danger_count", nullable = false)
    private Integer dangerCount;

    @Column(name = "manual_review_count", nullable = false)
    private Integer manualReviewCount;

    @Column(name = "inconclusive_count", nullable = false)
    private Integer inconclusiveCount;

    @Column(name = "plant_details_json", length = 20000)
    private String plantDetailsJson;

    @Column(name = "analysis_provider", length = 40)
    private String analysisProvider;

    @Column(name = "analysis_model", length = 80)
    private String analysisModel;

    @Column(name = "analysis_notes", length = 1000)
    private String analysisNotes;

    @Column(name = "pdf_path", length = 500)
    private String pdfPath;

    @Column(name = "public_share_token", unique = true, length = 64)
    private String publicShareToken;
}
