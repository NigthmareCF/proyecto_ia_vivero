package com.vivero.module.reports.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReportFindingDto {

    @NotBlank(message = "Finding side is required")
    @Size(max = 20, message = "Finding side must not exceed 20 characters")
    private String side;

    @Size(max = 500, message = "Finding note must not exceed 500 characters")
    private String note;
}
