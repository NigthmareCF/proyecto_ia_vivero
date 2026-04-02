package com.vivero.module.plants.repository;

import com.vivero.module.plants.entity.Plant;
import com.vivero.shared.enums.PlantState;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repositorio JPA del módulo plants.
 */
@Repository
public interface PlantRepository extends JpaRepository<Plant, Long> {

    Optional<Plant> findByQrCode(String qrCode);

    boolean existsByQrCode(String qrCode);

    boolean existsByQrCodeAndIdNot(String qrCode, Long id);

    List<Plant> findByCurrentState(PlantState currentState);
}