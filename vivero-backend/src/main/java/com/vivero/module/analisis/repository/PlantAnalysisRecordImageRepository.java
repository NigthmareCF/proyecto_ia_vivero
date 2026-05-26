package com.vivero.module.analisis.repository;

import com.vivero.module.analisis.entity.PlantAnalysisRecordImage;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PlantAnalysisRecordImageRepository extends JpaRepository<PlantAnalysisRecordImage, Long> {

    List<PlantAnalysisRecordImage> findByAnalysisRecordIdOrderBySortOrderAsc(Long analysisRecordId);
}
