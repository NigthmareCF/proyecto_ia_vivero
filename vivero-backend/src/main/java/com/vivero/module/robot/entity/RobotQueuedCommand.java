package com.vivero.module.robot.entity;

import com.vivero.shared.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "robot_queued_command")
public class RobotQueuedCommand extends BaseEntity {

    @Column(name = "robot_id", nullable = false, length = 80)
    private String robotId;

    @Column(name = "command_name", nullable = false, length = 80)
    private String commandName;

    @Column(name = "payload_json", columnDefinition = "TEXT")
    private String payloadJson;

    @Builder.Default
    @Column(name = "acknowledged", nullable = false)
    private boolean acknowledged = false;

    @Column(name = "acknowledged_at")
    private LocalDateTime acknowledgedAt;
}
