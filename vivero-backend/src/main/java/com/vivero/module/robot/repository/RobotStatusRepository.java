package com.vivero.module.robot.repository;

import com.vivero.module.robot.entity.RobotStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repositorio del estado del robot.
 */
@Repository
public interface RobotStatusRepository extends JpaRepository<RobotStatus, Long> {

    Optional<RobotStatus> findTopByOrderByLastSeenAtDesc();
}