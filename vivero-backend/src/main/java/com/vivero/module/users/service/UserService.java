package com.vivero.module.users.service;

import com.vivero.module.users.dto.UpdateRoleRequestDto;
import com.vivero.module.users.dto.UserRequestDto;
import com.vivero.module.users.dto.UserResponseDto;
import com.vivero.shared.enums.UserRole;

import java.util.List;

/**
 * Contrato del módulo de gestión de usuarios.
 */
public interface UserService {

    List<UserResponseDto> getAllUsers(UserRole role, Boolean active);

    UserResponseDto getUserById(Long id);

    UserResponseDto createUser(UserRequestDto request);

    UserResponseDto updateUser(Long id, UserRequestDto request, String currentUserEmail);

    UserResponseDto updateRole(Long id, UpdateRoleRequestDto request, String currentUserEmail);

    void deleteUser(Long id, String currentUserEmail);
}
