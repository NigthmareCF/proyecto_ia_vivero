package com.vivero.module.auth.dto;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class UpdateProfileRequestDto {

    @Size(max = 20, message = "Phone number must not exceed 20 characters")
    @Pattern(regexp = "^$|^\\+?[1-9]\\d{7,14}$", message = "Phone number must be valid")
    private String phoneNumber;
}
