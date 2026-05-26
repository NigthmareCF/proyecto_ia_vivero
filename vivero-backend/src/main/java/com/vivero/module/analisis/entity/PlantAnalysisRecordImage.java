package com.vivero.module.analisis.entity;

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
@Table(name = "plant_analysis_record_images")
public class PlantAnalysisRecordImage extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "analysis_record_id", nullable = false)
    private PlantAnalysisRecord analysisRecord;

    @Column(name = "file_path", nullable = false, length = 500)
    private String filePath;

    @Column(name = "mime_type", nullable = false, length = 80)
    private String mimeType;

    @Column(name = "sort_order", nullable = false)
    private Integer sortOrder;
}
