package com.vivero.module.analisis.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UuidGenerator;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "plant_reports", indexes = {
        @Index(name = "idx_plant_reports_created_at", columnList = "created_at")
})
public class PlantReport {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @Column(name = "imagen_url", length = 500, nullable = false)
    private String imagenUrl;

    @Column(name = "observaciones_operador", columnDefinition = "TEXT")
    private String observacionesOperador;

    @Column(name = "estado_general", length = 50, nullable = false)
    private String estadoGeneral;

    @Column(nullable = false, precision = 4, scale = 3)
    private BigDecimal confianza;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String hallazgos;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String diagnostico;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String recomendaciones;

    @Column(length = 20, nullable = false)
    private String urgencia;

    @Column(name = "modelo_ia", length = 50, nullable = false)
    private String modeloIa;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}
