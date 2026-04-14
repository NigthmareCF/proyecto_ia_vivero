# Modulo Analisis

1. El frontend envia imagen base64 y observaciones del operador a `POST /api/analisis/planta`.
2. `PlantAnalysisService` selecciona el proveedor Vision configurado (`gemini` u `openai`).
3. El diagnostico estructurado se persiste en `plant_reports`.
4. El backend publica el resultado en `/topic/analisis`.
5. Si la urgencia es `CRITICA`, tambien publica en `/topic/alertas`.
