package com.vivero.module.users.service.impl;

import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.users.dto.UpdateRoleRequestDto;
import com.vivero.module.users.dto.UserRequestDto;
import com.vivero.module.users.dto.UserResponseDto;
import com.vivero.module.users.mapper.UserMapper;
import com.vivero.module.users.service.UserService;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import com.vivero.shared.exception.ResourceNotFoundException;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;

/**
 * Implementación del módulo administrativo de usuarios.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final UserMapper userMapper;

    @Override
    @Transactional(readOnly = true)
    public List<UserResponseDto> getAllUsers(UserRole role, Boolean active) {
        List<User> users;

        if (role != null) {
            users = userRepository.findByRole(role);
        } else if (active != null) {
            users = userRepository.findByActive(active);
        } else {
            users = userRepository.findAll(Sort.by(Sort.Direction.DESC, "createdAt"));
        }

        if (role != null && active != null) {
            users = users.stream()
                    .filter(user -> user.isActive() == active)
                    .toList();
        }

        return users.stream()
                .map(userMapper::toResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public UserResponseDto getUserById(Long id) {
        return userMapper.toResponse(findUserOrThrow(id));
    }

    @Override
    @Transactional
    public UserResponseDto createUser(UserRequestDto request) {
        validatePasswordForCreate(request.getPassword());

        String normalizedEmail = normalizeEmail(request.getEmail());
        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new BusinessException(
                    "Email already registered: " + normalizedEmail,
                    "EMAIL_ALREADY_EXISTS"
            );
        }

        User user = Objects.requireNonNull(
                User.builder()
                        .firstName(request.getFirstName().trim())
                        .lastName(request.getLastName().trim())
                        .email(normalizedEmail)
                        .password(passwordEncoder.encode(request.getPassword()))
                        .role(request.getRole())
                        .active(Boolean.TRUE.equals(request.getActive()))
                        .build()
        );

        userRepository.save(user);
        log.info("Usuario creado desde módulo users: {}", user.getEmail());

        return userMapper.toResponse(user);
    }

    @Override
    @Transactional
    public UserResponseDto updateUser(Long id, UserRequestDto request, String currentUserEmail) {
        User user = findUserOrThrow(id);
        String normalizedEmail = normalizeEmail(request.getEmail());

        if (userRepository.existsByEmailAndIdNot(normalizedEmail, id)) {
            throw new BusinessException(
                    "Email already registered: " + normalizedEmail,
                    "EMAIL_ALREADY_EXISTS"
            );
        }

        if (isCurrentUser(user, currentUserEmail) && !Boolean.TRUE.equals(request.getActive())) {
            throw new BusinessException(
                    "You cannot deactivate your own account",
                    "SELF_DEACTIVATION_NOT_ALLOWED"
            );
        }

        user.setFirstName(request.getFirstName().trim());
        user.setLastName(request.getLastName().trim());
        user.setEmail(normalizedEmail);
        user.setRole(request.getRole());
        user.setActive(Boolean.TRUE.equals(request.getActive()));

        if (hasText(request.getPassword())) {
            user.setPassword(passwordEncoder.encode(request.getPassword()));
        }

        log.info("Usuario actualizado: {}", user.getEmail());
        return userMapper.toResponse(user);
    }

    @Override
    @Transactional
    public UserResponseDto updateRole(Long id, UpdateRoleRequestDto request, String currentUserEmail) {
        User user = findUserOrThrow(id);

        if (isCurrentUser(user, currentUserEmail)) {
            throw new BusinessException(
                    "You cannot change your own role",
                    "SELF_ROLE_CHANGE_NOT_ALLOWED"
            );
        }

        user.setRole(request.getRole());
        log.info("Rol actualizado para {}: {}", user.getEmail(), user.getRole());
        return userMapper.toResponse(user);
    }

    @Override
    @Transactional
    public void deleteUser(Long id, String currentUserEmail) {
        User user = findUserOrThrow(id);

        if (isCurrentUser(user, currentUserEmail)) {
            throw new BusinessException(
                    "You cannot delete your own account",
                    "SELF_DELETE_NOT_ALLOWED"
            );
        }

        userRepository.delete(user);
        log.info("Usuario eliminado: {}", user.getEmail());
    }

    private @NonNull User findUserOrThrow(@NonNull Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with id: " + id));
    }

    private void validatePasswordForCreate(String password) {
        if (!hasText(password)) {
            throw new BusinessException("Password is required", "PASSWORD_REQUIRED");
        }
    }

    private boolean isCurrentUser(@NonNull User user, String currentUserEmail) {
        return user.getEmail().equalsIgnoreCase(currentUserEmail);
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private String normalizeEmail(String email) {
        return email.trim().toLowerCase();
    }
}