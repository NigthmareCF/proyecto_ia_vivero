package com.vivero.module.robot.entity;

import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.RobotMode;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * Estado persistido más reciente del robot.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "robot_status")
public class RobotStatus extends BaseEntity {

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private RobotMode mode = RobotMode.IDLE;

    @Column(name = "battery_level")
    private Integer batteryLevel;

    @Column(name = "current_plant_qr", length = 120)
    private String currentPlantQr;

    @Column(name = "is_connected", nullable = false)
    @Builder.Default
    private boolean connected = false;

    @Column(name = "last_seen_at", nullable = false)
    private LocalDateTime lastSeenAt;

    @Column(name = "last_command", length = 40)
    private String lastCommand;
}