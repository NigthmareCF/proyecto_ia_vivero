package com.vivero.module.analisis.dto;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class PlantAnalysisHistoryImageDto {

    private Long id;
    private String imageUrl;
    private String mimeType;
    private Integer sortOrder;
}
