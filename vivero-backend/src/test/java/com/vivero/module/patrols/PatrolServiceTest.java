package com.vivero.module.patrols;

import com.vivero.module.auth.entity.User;
import com.vivero.module.auth.repository.UserRepository;
import com.vivero.module.patrols.dto.PatrolResponseDto;
import com.vivero.module.patrols.dto.PatrolResultRequestDto;
import com.vivero.module.patrols.dto.StartPatrolRequestDto;
import com.vivero.module.patrols.entity.Observation;
import com.vivero.module.patrols.entity.Patrol;
import com.vivero.module.patrols.mapper.PatrolMapper;
import com.vivero.module.patrols.repository.ObservationRepository;
import com.vivero.module.patrols.repository.PatrolRepository;
import com.vivero.module.patrols.service.impl.PatrolServiceImpl;
import com.vivero.shared.enums.PatrolFilter;
import com.vivero.shared.enums.PatrolMode;
import com.vivero.shared.enums.PatrolStatus;
import com.vivero.shared.enums.PlantState;
import com.vivero.shared.enums.UserRole;
import com.vivero.shared.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mapstruct.factory.Mappers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Objects;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PatrolServiceTest {

    @Mock
    private PatrolRepository patrolRepository;

    @Mock
    private ObservationRepository observationRepository;

    @Mock
    private UserRepository userRepository;

    private PatrolServiceImpl patrolService;

    @BeforeEach
    void setUp() {
        PatrolMapper patrolMapper = Mappers.getMapper(PatrolMapper.class);
        patrolService = new PatrolServiceImpl(patrolRepository, observationRepository, userRepository, patrolMapper);
    }

    @Test
    void startPatrolShouldCreatePatrolInProgress() {
        User user = User.builder()
                .firstName("System")
                .lastName("Admin")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        StartPatrolRequestDto request = new StartPatrolRequestDto();
        request.setMode(PatrolMode.AUTO);
        request.setFilter(PatrolFilter.ALL);

        when(userRepository.findByEmail("admin@vivero.com")).thenReturn(Optional.of(user));
        when(patrolRepository.save(argThat(Objects::nonNull))).thenAnswer(invocation -> invocation.getArgument(0, Patrol.class));

        PatrolResponseDto response = patrolService.startPatrol(request, "admin@vivero.com");

        assertEquals(PatrolStatus.IN_PROGRESS, response.getStatus());
        assertEquals(PatrolMode.AUTO, response.getMode());
        verify(patrolRepository).save(argThat(Objects::nonNull));
    }

    @Test
    void registerResultShouldRejectPatrolOutsideInProgress() {
        User user = User.builder()
                .firstName("System")
                .lastName("Admin")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        Patrol patrol = Patrol.builder()
                .startedBy(user)
                .mode(PatrolMode.AUTO)
                .filter(PatrolFilter.ALL)
                .status(PatrolStatus.COMPLETED)
                .startedAt(LocalDateTime.now())
                .observations(new ArrayList<>())
                .build();
        patrol.setId(10L);

        PatrolResultRequestDto request = new PatrolResultRequestDto();
        request.setPlantQrCode("QR-001");
        request.setAiResult(PlantState.HEALTHY);
        request.setAiConfidence(0.91);

        when(patrolRepository.findById(10L)).thenReturn(Optional.of(patrol));

        BusinessException exception = assertThrows(BusinessException.class,
                () -> patrolService.registerResult(10L, request));

        assertEquals("PATROL_NOT_IN_PROGRESS", exception.getCode());
    }

    @Test
    void completePatrolShouldClosePatrol() {
        User user = User.builder()
                .firstName("System")
                .lastName("Admin")
                .email("admin@vivero.com")
                .password("secret")
                .role(UserRole.ADMIN)
                .active(true)
                .build();

        Patrol patrol = Patrol.builder()
                .startedBy(user)
                .mode(PatrolMode.AUTO)
                .filter(PatrolFilter.ATTENTION)
                .status(PatrolStatus.IN_PROGRESS)
                .startedAt(LocalDateTime.now())
                .observations(new ArrayList<Observation>())
                .build();
        patrol.setId(11L);

        when(patrolRepository.findById(11L)).thenReturn(Optional.of(patrol));

        PatrolResponseDto response = patrolService.completePatrol(11L);

        assertEquals(PatrolStatus.COMPLETED, response.getStatus());
    }
}