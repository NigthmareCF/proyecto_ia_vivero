package com.vivero.module.plants.entity;

import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.PlantState;
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

/**
 * Entidad principal de plantas registradas en el vivero.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "plants")
public class Plant extends BaseEntity {

    @Column(name = "qr_code", nullable = false, unique = true, length = 120)
    private String qrCode;

    @Column(nullable = false, length = 150)
    private String name;

    @Column(nullable = false, length = 150)
    private String location;

    @Column(length = 500)
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(name = "current_state", nullable = false, length = 20)
    @Builder.Default
    private PlantState currentState = PlantState.UNKNOWN;
}
