package com.vivero.module.analisis.entity;

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

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "plant_analysis_records")
public class PlantAnalysisRecord extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "generated_by", nullable = false)
    private User generatedBy;

    @Column(name = "source_type", nullable = false, length = 30)
    private String sourceType;

    @Column(name = "estado_general", nullable = false, length = 40)
    private String estadoGeneral;

    @Column(nullable = false, length = 40)
    private String urgencia;

    @Column(nullable = false)
    private Double confianza;

    @Column(name = "summary_text", length = 6000)
    private String summaryText;

    @Column(name = "hallazgos_json", length = 12000)
    private String hallazgosJson;

    @Column(name = "recomendaciones_json", length = 12000)
    private String recomendacionesJson;

    @Column(name = "operator_notes", length = 3000)
    private String operatorNotes;

    @Column(name = "general_labels_json", length = 4000)
    private String generalLabelsJson;

    @Column(name = "exact_labels_json", length = 4000)
    private String exactLabelsJson;

    @Column(name = "primary_general_label", length = 120)
    private String primaryGeneralLabel;

    @Column(name = "primary_exact_label", length = 120)
    private String primaryExactLabel;

    @Column(name = "patrol_id")
    private Long patrolId;

    @Column(name = "report_id")
    private Long reportId;

    @Column(name = "report_title_snapshot", length = 150)
    private String reportTitleSnapshot;

    @Column(name = "modelo_ia", length = 120)
    private String modeloIa;

    @Column(name = "proveedor_ia", length = 80)
    private String proveedorIa;

    @Column(name = "requiere_revision_manual", nullable = false)
    private boolean requiereRevisionManual;

    @Column(nullable = false)
    private boolean fallback;
}
