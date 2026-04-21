package com.vivero.module.reports.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;

@Getter
@Setter
public class ReportPlantDetailDto {

    @NotBlank(message = "Plant group code is required")
    @Size(max = 120, message = "Plant group code must not exceed 120 characters")
    private String plantGroupCode;

    @NotBlank(message = "Final state is required")
    @Size(max = 40, message = "Final state must not exceed 40 characters")
    private String finalState;

    @Size(max = 600, message = "Plant summary must not exceed 600 characters")
    private String summary;

    @Valid
    private List<ReportFindingDto> findings = new ArrayList<>();
}
