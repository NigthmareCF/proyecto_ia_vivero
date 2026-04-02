package com.vivero.module.users.controller;

import com.vivero.module.users.dto.UpdateRoleRequestDto;
import com.vivero.module.users.dto.UserRequestDto;
import com.vivero.module.users.dto.UserResponseDto;
import com.vivero.module.users.service.UserService;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * API REST para la administración de usuarios.
 * Este módulo queda reservado para administradores.
 */
@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@PreAuthorize("hasRole('ADMIN')")
public class UserController {

    private final UserService userService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<UserResponseDto>>> getAllUsers(
            @RequestParam(required = false) UserRole role,
            @RequestParam(required = false) Boolean active) {

        List<UserResponseDto> users = userService.getAllUsers(role, active);
        return ResponseEntity.ok(ApiResponse.ok("Users retrieved successfully", users));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<UserResponseDto>> getUserById(@PathVariable Long id) {
        UserResponseDto user = userService.getUserById(id);
        return ResponseEntity.ok(ApiResponse.ok("User retrieved successfully", user));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<UserResponseDto>> createUser(
            @Valid @RequestBody UserRequestDto request) {

        UserResponseDto user = userService.createUser(request);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.ok("User created successfully", user));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<UserResponseDto>> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UserRequestDto request,
            Authentication authentication) {

        UserResponseDto user = userService.updateUser(id, request, authentication.getName());
        return ResponseEntity.ok(ApiResponse.ok("User updated successfully", user));
    }

    @PutMapping("/{id}/role")
    public ResponseEntity<ApiResponse<UserResponseDto>> updateRole(
            @PathVariable Long id,
            @Valid @RequestBody UpdateRoleRequestDto request,
            Authentication authentication) {

        UserResponseDto user = userService.updateRole(id, request, authentication.getName());
        return ResponseEntity.ok(ApiResponse.ok("User role updated successfully", user));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteUser(
            @PathVariable Long id,
            Authentication authentication) {

        userService.deleteUser(id, authentication.getName());
        return ResponseEntity.ok(ApiResponse.ok("User deleted successfully", null));
    }
}
