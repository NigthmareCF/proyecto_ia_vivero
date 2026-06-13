package com.vivero.module.auth.service.impl;

import com.vivero.module.auth.dto.AdminUpdatePasswordRequestDto;
import com.vivero.module.auth.dto.AdminUpdateUserRequestDto;
import com.vivero.module.auth.dto.UserAdminResponseDto;
import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.auth.service.UserAdminService;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserAdminServiceImpl implements UserAdminService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public List<UserAdminResponseDto> listUsers() {
        return userRepository.findAll().stream().map(this::toDto).toList();
    }

    @Override
    @Transactional
    public UserAdminResponseDto updateUser(Long userId, AdminUpdateUserRequestDto request) {
        User user = findUser(userId);

        boolean emailChanged = !user.getEmail().equalsIgnoreCase(request.getEmail().trim());
        if (emailChanged && userRepository.existsByEmail(request.getEmail().trim())) {
            throw new BusinessException("Email already registered: " + request.getEmail(), "EMAIL_ALREADY_EXISTS");
        }

        user.setFirstName(request.getFirstName().trim());
        user.setLastName(request.getLastName().trim());
        user.setEmail(request.getEmail().trim());
        user.setPhoneNumber(normalizePhone(request.getPhoneNumber()));
        if (request.getRole() != null) {
            user.setRole(request.getRole());
        }
        if (request.getActive() != null) {
            user.setActive(request.getActive());
        }

        return toDto(userRepository.save(user));
    }

    @Override
    @Transactional
    public UserAdminResponseDto updatePassword(Long userId, AdminUpdatePasswordRequestDto request) {
        User user = findUser(userId);
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        return toDto(userRepository.save(user));
    }

    @Override
    @Transactional
    public void deleteUser(Long userId) {
        User user = findUser(userId);
        userRepository.delete(user);
    }

    private User findUser(Long userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
    }

    private UserAdminResponseDto toDto(User user) {
        return UserAdminResponseDto.builder()
                .id(user.getId())
                .firstName(user.getFirstName())
                .lastName(user.getLastName())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phoneNumber(user.getPhoneNumber())
                .role(user.getRole())
                .active(user.isActive())
                .build();
    }

    private String normalizePhone(String value) {
        if (value == null || value.trim().isEmpty()) {
            return null;
        }
        return value.trim();
    }
}
