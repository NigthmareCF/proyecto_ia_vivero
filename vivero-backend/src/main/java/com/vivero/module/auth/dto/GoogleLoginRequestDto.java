package com.vivero.module.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class GoogleLoginRequestDto {

    @NotBlank(message = "idToken is required")
    private String idToken;
}
