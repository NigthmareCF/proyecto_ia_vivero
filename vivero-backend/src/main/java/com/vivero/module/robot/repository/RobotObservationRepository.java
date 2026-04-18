package com.vivero.module.robot.repository;

import com.vivero.module.robot.entity.RobotObservation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Repositorio de observaciones capturadas por el robot.
 */
@Repository
public interface RobotObservationRepository extends JpaRepository<RobotObservation, Long> {
}
