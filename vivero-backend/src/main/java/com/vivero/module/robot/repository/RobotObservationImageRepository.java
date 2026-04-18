package com.vivero.module.robot.repository;

import com.vivero.module.robot.entity.RobotObservationImage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Repositorio de imágenes asociadas a observaciones del robot.
 */
@Repository
public interface RobotObservationImageRepository extends JpaRepository<RobotObservationImage, Long> {
}
