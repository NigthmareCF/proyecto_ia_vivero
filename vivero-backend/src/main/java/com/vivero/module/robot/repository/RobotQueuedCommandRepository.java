package com.vivero.module.robot.repository;

import com.vivero.module.robot.entity.RobotQueuedCommand;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RobotQueuedCommandRepository extends JpaRepository<RobotQueuedCommand, Long> {

    Optional<RobotQueuedCommand> findTopByRobotIdAndAcknowledgedFalseOrderByCreatedAtAsc(String robotId);
}
