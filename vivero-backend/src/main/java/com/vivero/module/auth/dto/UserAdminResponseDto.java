package com.vivero.module.auth.dto;

import com.vivero.shared.enums.UserRole;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserAdminResponseDto {
    private Long id;
    private String firstName;
    private String lastName;
    private String fullName;
    private String email;
    private String phoneNumber;
    private UserRole role;
    private boolean active;
}
