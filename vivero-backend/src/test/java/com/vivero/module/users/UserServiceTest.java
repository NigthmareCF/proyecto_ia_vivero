package com.vivero.module.users;

import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.users.dto.UpdateRoleRequestDto;
import com.vivero.module.users.dto.UserRequestDto;
import com.vivero.module.users.dto.UserResponseDto;
import com.vivero.module.users.mapper.UserMapper;
import com.vivero.module.users.service.impl.UserServiceImpl;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mapstruct.factory.Mappers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    private UserServiceImpl userService;

    @BeforeEach
    void setUp() {
        UserMapper userMapper = Mappers.getMapper(UserMapper.class);
        userService = new UserServiceImpl(userRepository, passwordEncoder, userMapper);
    }

    @Test
    void createUserShouldEncodePasswordAndPersistUser() {
        UserRequestDto request = new UserRequestDto();
        request.setFirstName("Ana");
        request.setLastName("Lopez");
        request.setEmail("ANA@VIVERO.COM");
        request.setPassword("Password123");
        request.setRole(UserRole.OPERATOR);
        request.setActive(true);

        when(userRepository.existsByEmail("ana@vivero.com")).thenReturn(false);
        when(passwordEncoder.encode("Password123")).thenReturn("encoded-password");
        when(userRepository.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        UserResponseDto response = userService.createUser(request);

        assertEquals("ana@vivero.com", response.getEmail());
        assertEquals(UserRole.OPERATOR, response.getRole());
        verify(passwordEncoder).encode("Password123");
        verify(userRepository).save(any(User.class));
    }

    @Test
    void updateUserShouldRejectSelfDeactivation() {
        User existingUser = User.builder()
                .firstName("System")
                .lastName("Admin")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();
        existingUser.setId(1L);

        UserRequestDto request = new UserRequestDto();
        request.setFirstName("System");
        request.setLastName("Admin");
        request.setEmail("admin@vivero.com");
        request.setRole(UserRole.ADMIN);
        request.setActive(false);

        when(userRepository.findById(1L)).thenReturn(Optional.of(existingUser));
        when(userRepository.existsByEmailAndIdNot("admin@vivero.com", 1L)).thenReturn(false);

        BusinessException exception = assertThrows(BusinessException.class,
                () -> userService.updateUser(1L, request, "admin@vivero.com"));

        assertEquals("SELF_DEACTIVATION_NOT_ALLOWED", exception.getCode());
    }

    @Test
    void updateRoleShouldRejectOwnRoleChange() {
        User existingUser = User.builder()
                .firstName("System")
                .lastName("Admin")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();
        existingUser.setId(1L);

        UpdateRoleRequestDto request = new UpdateRoleRequestDto();
        request.setRole(UserRole.VIEWER);

        when(userRepository.findById(1L)).thenReturn(Optional.of(existingUser));

        BusinessException exception = assertThrows(BusinessException.class,
                () -> userService.updateRole(1L, request, "admin@vivero.com"));

        assertEquals("SELF_ROLE_CHANGE_NOT_ALLOWED", exception.getCode());
    }
}
