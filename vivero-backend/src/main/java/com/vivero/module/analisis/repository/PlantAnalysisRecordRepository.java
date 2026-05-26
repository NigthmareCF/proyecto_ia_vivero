package com.vivero.module.analisis.repository;

import com.vivero.module.analisis.entity.PlantAnalysisRecord;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PlantAnalysisRecordRepository extends JpaRepository<PlantAnalysisRecord, Long> {

    List<PlantAnalysisRecord> findAllByOrderByCreatedAtDesc();
}
