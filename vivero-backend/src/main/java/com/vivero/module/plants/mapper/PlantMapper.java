package com.vivero.module.plants.mapper;

import com.vivero.module.plants.dto.PlantResponseDto;
import com.vivero.module.plants.entity.Plant;
import org.mapstruct.Mapper;

/**
 * Mapper entre entidad Plant y su DTO de salida.
 */
@Mapper(componentModel = "spring")
public interface PlantMapper {

    PlantResponseDto toResponse(Plant plant);
}