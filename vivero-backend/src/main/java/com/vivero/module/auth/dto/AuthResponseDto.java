package com.vivero.module.auth.dto;

import com.vivero.shared.enums.AuthProvider;
import com.vivero.shared.enums.UserRole;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuthResponseDto {

    private String accessToken;
    private String refreshToken;

    @Builder.Default
    private String tokenType = "Bearer";

    private Long userId;
    private String fullName;
    private String email;
    private UserRole role;
    private AuthProvider authProvider;
}
