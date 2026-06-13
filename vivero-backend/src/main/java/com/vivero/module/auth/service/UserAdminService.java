package com.vivero.module.auth.service;

import com.vivero.module.auth.dto.AdminUpdatePasswordRequestDto;
import com.vivero.module.auth.dto.AdminUpdateUserRequestDto;
import com.vivero.module.auth.dto.UserAdminResponseDto;

import java.util.List;

public interface UserAdminService {
    List<UserAdminResponseDto> listUsers();

    UserAdminResponseDto updateUser(Long userId, AdminUpdateUserRequestDto request);

    UserAdminResponseDto updatePassword(Long userId, AdminUpdatePasswordRequestDto request);

    void deleteUser(Long userId);
}
