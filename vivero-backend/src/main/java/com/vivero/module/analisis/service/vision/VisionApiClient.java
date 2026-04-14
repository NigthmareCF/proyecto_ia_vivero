package com.vivero.module.analisis.service.vision;

public interface VisionApiClient {

    VisionDiagnosis analyzePlantImage(String imageBase64, String mimeType, String operatorNotes);
}
