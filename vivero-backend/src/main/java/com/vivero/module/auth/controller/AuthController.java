package com.vivero.module.auth.controller;

import com.vivero.module.auth.dto.AuthResponseDto;
import com.vivero.module.auth.dto.LoginRequestDto;
import com.vivero.module.auth.dto.RefreshTokenRequestDto;
import com.vivero.module.auth.dto.RegisterRequestDto;
import com.vivero.module.auth.dto.UpdateProfileRequestDto;
import com.vivero.module.auth.service.AuthService;
import com.vivero.shared.response.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponseDto>> login(@Valid @RequestBody LoginRequestDto request) {
        AuthResponseDto response = authService.login(request);
        return ResponseEntity.ok(ApiResponse.ok("Login successful", response));
    }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponseDto>> register(@Valid @RequestBody RegisterRequestDto request) {
        AuthResponseDto response = authService.register(request);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ApiResponse.ok("User registered successfully", response));
    }

    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<AuthResponseDto>> refresh(@Valid @RequestBody RefreshTokenRequestDto request) {
        AuthResponseDto response = authService.refresh(request);
        return ResponseEntity.ok(ApiResponse.ok("Token refreshed successfully", response));
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<AuthResponseDto>> me(
            org.springframework.security.core.Authentication authentication
    ) {
        com.vivero.module.auth.entity.User user =
                (com.vivero.module.auth.entity.User) authentication.getPrincipal();

        AuthResponseDto response = AuthResponseDto.builder()
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .role(user.getRole())
                .build();

        return ResponseEntity.ok(ApiResponse.ok("User data retrieved", response));
    }

    @PatchMapping("/me")
    public ResponseEntity<ApiResponse<AuthResponseDto>> updateProfile(
            org.springframework.security.core.Authentication authentication,
            @Valid @RequestBody UpdateProfileRequestDto request
    ) {
        com.vivero.module.auth.entity.User user =
                (com.vivero.module.auth.entity.User) authentication.getPrincipal();
        AuthResponseDto response = authService.updateProfile(user.getEmail(), request);
        return ResponseEntity.ok(ApiResponse.ok("Profile updated", response));
    }
}
