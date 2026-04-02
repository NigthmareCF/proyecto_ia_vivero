package com.vivero.module.patrols.mapper;

import com.vivero.module.patrols.dto.PatrolResponseDto;
import com.vivero.module.patrols.entity.Patrol;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

/**
 * Mapper de salida del módulo patrols.
 */
@Mapper(componentModel = "spring")
public interface PatrolMapper {

    @Mapping(target = "startedByEmail", expression = "java(patrol.getStartedBy().getEmail())")
    @Mapping(target = "startedByName", expression = "java(patrol.getStartedBy().getFullName())")
    @Mapping(target = "observationsCount", expression = "java(patrol.getObservations() != null ? patrol.getObservations().size() : 0)")
    PatrolResponseDto toResponse(Patrol patrol);
}