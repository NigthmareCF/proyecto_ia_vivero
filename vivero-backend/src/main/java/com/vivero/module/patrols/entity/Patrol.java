package com.vivero.module.patrols.entity;

import com.vivero.module.auth.entity.User;
import com.vivero.shared.entity.BaseEntity;
import com.vivero.shared.enums.PatrolFilter;
import com.vivero.shared.enums.PatrolMode;
import com.vivero.shared.enums.PatrolStatus;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Entidad principal de un patrullaje ejecutado por el robot.
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "patrols")
public class Patrol extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "started_by", nullable = false)
    private User startedBy;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private PatrolMode mode;

    @Enumerated(EnumType.STRING)
    @Column(name = "filter_type", nullable = false, length = 20)
    @Builder.Default
    private PatrolFilter filter = PatrolFilter.ALL;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private PatrolStatus status = PatrolStatus.PENDING;

    @Column(name = "started_at", nullable = false)
    private LocalDateTime startedAt;

    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    @OneToMany(mappedBy = "patrol", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Observation> observations = new ArrayList<>();
}