package com.vivero.module.robot.repository;

import com.vivero.module.robot.entity.RobotObservation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Repositorio de observaciones capturadas por el robot.
 */
@Repository
public interface RobotObservationRepository extends JpaRepository<RobotObservation, Long> {
    java.util.List<RobotObservation> findByPatrolIdOrderByObservedAtAsc(String patrolId);
    java.util.List<RobotObservation> findByPatrolIdAndOperationalDateOrderByScanSequenceAsc(String patrolId, java.time.LocalDate operationalDate);
    long countByPatrolIdAndOperationalDate(String patrolId, java.time.LocalDate operationalDate);
    java.util.Optional<RobotObservation> findTopByPlantGroupCodeOrderByObservedAtDesc(String plantGroupCode);
    java.util.Optional<RobotObservation> findTopByPlantQrOrderByObservedAtDesc(String plantQr);
    java.util.List<RobotObservation> findByFinalStateOrderByObservedAtDesc(String finalState);
}
