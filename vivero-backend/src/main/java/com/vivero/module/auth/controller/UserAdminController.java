package com.vivero.module.auth.controller;

import com.vivero.module.auth.dto.AdminUpdatePasswordRequestDto;
import com.vivero.module.auth.dto.AdminUpdateUserRequestDto;
import com.vivero.module.auth.dto.UserAdminResponseDto;
import com.vivero.module.auth.service.UserAdminService;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
public class UserAdminController {

    private final UserAdminService userAdminService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<UserAdminResponseDto>>> listUsers() {
        return ResponseEntity.ok(ApiResponse.ok("Users retrieved", userAdminService.listUsers()));
    }

    @PatchMapping("/{userId}")
    public ResponseEntity<ApiResponse<UserAdminResponseDto>> updateUser(
            @PathVariable Long userId,
            @Valid @RequestBody AdminUpdateUserRequestDto request
    ) {
        return ResponseEntity.ok(ApiResponse.ok("User updated", userAdminService.updateUser(userId, request)));
    }

    @PatchMapping("/{userId}/password")
    public ResponseEntity<ApiResponse<UserAdminResponseDto>> updatePassword(
            @PathVariable Long userId,
            @Valid @RequestBody AdminUpdatePasswordRequestDto request
    ) {
        return ResponseEntity.ok(ApiResponse.ok("Password updated", userAdminService.updatePassword(userId, request)));
    }

    @DeleteMapping("/{userId}")
    public ResponseEntity<ApiResponse<Void>> deleteUser(@PathVariable Long userId) {
        userAdminService.deleteUser(userId);
        return ResponseEntity.ok(ApiResponse.ok("User deleted", null));
    }
}
