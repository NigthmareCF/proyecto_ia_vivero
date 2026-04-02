package com.vivero.module.users.mapper;

import com.vivero.module.auth.entity.User;
import com.vivero.module.users.dto.UserResponseDto;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

/**
 * Mapeador entre entidad User y su DTO de respuesta administrativo.
 */
@Mapper(componentModel = "spring")
public interface UserMapper {

    @Mapping(target = "fullName", expression = "java(user.getFullName())")
    UserResponseDto toResponse(User user);
}
