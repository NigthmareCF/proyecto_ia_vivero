package com.vivero.module.robot.repository;

import com.vivero.module.robot.entity.RobotObservationImage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Repositorio de imagenes asociadas a observaciones del robot.
 */
@Repository
public interface RobotObservationImageRepository extends JpaRepository<RobotObservationImage, Long> {
    List<RobotObservationImage> findByObservationIdOrderBySortOrderAsc(Long observationId);
}
