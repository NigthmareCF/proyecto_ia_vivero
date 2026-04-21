package com.vivero.module.reports.repository;

import com.vivero.module.reports.entity.Report;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repositorio JPA para reportes generados.
 */
@Repository
public interface ReportRepository extends JpaRepository<Report, Long> {

    List<Report> findAllByOrderByCreatedAtDesc();

    Optional<Report> findByPublicShareToken(String publicShareToken);
}
