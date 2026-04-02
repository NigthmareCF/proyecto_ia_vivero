package com.vivero.module.plants;

import com.vivero.module.plants.dto.PlantRequestDto;
import com.vivero.module.plants.dto.PlantResponseDto;
import com.vivero.module.plants.entity.Plant;
import com.vivero.module.plants.mapper.PlantMapper;
import com.vivero.module.plants.repository.PlantRepository;
import com.vivero.module.plants.service.impl.PlantServiceImpl;
import com.vivero.shared.enums.PlantState;
import com.vivero.shared.exception.BusinessException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mapstruct.factory.Mappers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Objects;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class PlantServiceTest {

    @Mock
    private PlantRepository plantRepository;

    private PlantServiceImpl plantService;

    @BeforeEach
    void setUp() {
        PlantMapper plantMapper = Mappers.getMapper(PlantMapper.class);
        plantService = new PlantServiceImpl(plantRepository, plantMapper);
    }

    @Test
    void createPlantShouldNormalizeQrAndPersistPlant() {
        PlantRequestDto request = new PlantRequestDto();
        request.setQrCode(" qr-001 ");
        request.setName("Chile 1");
        request.setLocation("Fila A - Maceta 1");
        request.setDescription("Planta inicial");
        request.setCurrentState(PlantState.UNKNOWN);

        when(plantRepository.existsByQrCode("QR-001")).thenReturn(false);
        when(plantRepository.save(argThat(Objects::nonNull))).thenAnswer(invocation -> invocation.getArgument(0, Plant.class));

        PlantResponseDto response = plantService.createPlant(request);

        assertEquals("QR-001", response.getQrCode());
        assertEquals(PlantState.UNKNOWN, response.getCurrentState());
        verify(plantRepository).save(argThat(Objects::nonNull));
    }

    @Test
    void createPlantShouldRejectDuplicatedQrCode() {
        PlantRequestDto request = new PlantRequestDto();
        request.setQrCode("QR-001");
        request.setName("Chile 1");
        request.setLocation("Fila A - Maceta 1");
        request.setCurrentState(PlantState.HEALTHY);

        when(plantRepository.existsByQrCode("QR-001")).thenReturn(true);

        BusinessException exception = assertThrows(BusinessException.class,
                () -> plantService.createPlant(request));

        assertEquals("PLANT_QR_ALREADY_EXISTS", exception.getCode());
    }

    @Test
    void getPlantByQrCodeShouldReturnPlant() {
        Plant plant = Plant.builder()
                .qrCode("QR-123")
                .name("Chile 2")
                .location("Fila B - Maceta 3")
                .description("Sin novedades")
                .currentState(PlantState.ATTENTION)
                .build();

        when(plantRepository.findByQrCode("QR-123")).thenReturn(Optional.of(plant));

        PlantResponseDto response = plantService.getPlantByQrCode(" qr-123 ");

        assertEquals("QR-123", response.getQrCode());
        assertEquals(PlantState.ATTENTION, response.getCurrentState());
    }
}