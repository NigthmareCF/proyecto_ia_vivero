package com.vivero.module.patrols.repository;

import com.vivero.module.patrols.entity.Patrol;
import com.vivero.shared.enums.PatrolStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Repositorio JPA del módulo patrols.
 */
@Repository
public interface PatrolRepository extends JpaRepository<Patrol, Long> {

    List<Patrol> findByStatus(PatrolStatus status);
}