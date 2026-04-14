package com.vivero.module.auth.dto;

import com.vivero.shared.enums.AuthProvider;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class SocialLoginRequestDto {

    @NotNull(message = "Social provider is required")
    private AuthProvider provider;

    @NotBlank(message = "ID token is required")
    private String idToken;
}
