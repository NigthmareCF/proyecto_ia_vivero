package com.vivero.module.analisis.repository;

import com.vivero.module.analisis.entity.PlantReport;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface PlantReportRepository extends JpaRepository<PlantReport, UUID> {
}
