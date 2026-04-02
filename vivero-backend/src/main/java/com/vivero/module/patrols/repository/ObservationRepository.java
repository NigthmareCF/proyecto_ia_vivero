package com.vivero.module.patrols.repository;

import com.vivero.module.patrols.entity.Observation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Repositorio de observaciones generadas durante patrullajes.
 */
@Repository
public interface ObservationRepository extends JpaRepository<Observation, Long> {

    List<Observation> findByPatrolId(Long patrolId);
}