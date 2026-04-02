package com.vivero.module.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Datos que el cliente envía para iniciar sesión.
 * @NotBlank y @Email se validan automáticamente gracias a spring-boot-starter-validation.
 * Si fallan, GlobalExceptionHandler devuelve un 400 con los campos inválidos.
 */
@Data
public class LoginRequestDto {

    @NotBlank(message = "Email is required")
    @Email(message = "Email must be valid")
    private String email;

    @NotBlank(message = "Password is required")
    private String password;
}