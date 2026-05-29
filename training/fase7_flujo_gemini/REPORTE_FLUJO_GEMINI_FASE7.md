# Fase 7: flujo recomendado con Gemini

Fecha: 2026-05-28 06:32:23
Reglas fase 6: `C:\Proyecto_IA_Vivero\training\fase6_decision_confianza\decision_confianza_fase6.json`

## Estado actual

- El backend actual usa `POST /api/analisis/planta`.
- El servicio `PlantAnalysisServiceImpl` manda una imagen a Gemini y persiste un `PlantAnalysisRecord`.
- Publica resultados en `/topic/analisis` y alertas en `/topic/alertas`.
- Todavia no existe un endpoint de analisis por grupo de imagenes.

## Decision de fase 7

Gemini no debe llamarse por cada imagen si el robot captura muchas fotos. La llamada correcta es por grupo `planta + maceta + lado`, despues de que el clasificador local filtre y priorice evidencia.

Como fase 5 no aprobo ningun modelo local para diagnostico final, el modelo local queda solo como filtro rapido. Gemini o revision manual siguen siendo obligatorios para el diagnostico final.

## Flujo recomendado

1. Robot captura imagenes y las envia con contexto de QR/planta/maceta/lado.
2. Backend agrupa por planta + maceta + lado.
3. Modelo local clasifica cada imagen rapido y produce clase + confianza.
4. Backend aplica reglas de fase 6 por imagen y por grupo.
5. Backend selecciona 1 a 3 imagenes representativas si debe escalar.
6. Gemini analiza solo el grupo seleccionado o casos ambiguos.
7. Backend persiste resultado final y publica WebSocket.

## Cuando llamar Gemini

- grupo con peligro preliminar
- grupo ambiguo con mezcla sano/peligro
- grupo cuya clase ganadora sea atencion
- confianza promedio < 0.60
- menos de 3 imagenes utiles
- captura borrosa o evidencia insuficiente

## Cuando se podria omitir Gemini

Solo cuando todas estas condiciones sean verdaderas:

- modelo local aprobado en fase 5
- >= 3 imagenes utiles del grupo
- confianza promedio >= 0.80
- voto consistente entre imagenes
- sin contradiccion sano/peligro

En el estado actual del proyecto, esa omision no esta permitida para diagnostico final porque `modelo_local_aprobado_fase5` es `false`.

## Contrato sugerido

```json
{
  "current_backend": {
    "endpoint": "POST /api/analisis/planta",
    "mode": "single_image_to_gemini",
    "service": "PlantAnalysisServiceImpl.resolveAnalysis -> callGemini",
    "persistence": "PlantAnalysisRecord + PlantAnalysisRecordImage",
    "websocket_topics": [
      "/topic/analisis",
      "/topic/alertas"
    ],
    "limitation": "No agrupa imagenes por planta/maceta/lado antes de llamar a Gemini."
  },
  "recommended_flow": [
    "Robot captura imagenes y las envia con contexto de QR/planta/maceta/lado.",
    "Backend agrupa por planta + maceta + lado.",
    "Modelo local clasifica cada imagen rapido y produce clase + confianza.",
    "Backend aplica reglas de fase 6 por imagen y por grupo.",
    "Backend selecciona 1 a 3 imagenes representativas si debe escalar.",
    "Gemini analiza solo el grupo seleccionado o casos ambiguos.",
    "Backend persiste resultado final y publica WebSocket."
  ],
  "gemini_trigger_rules": {
    "always_trigger": [
      "grupo con peligro preliminar",
      "grupo ambiguo con mezcla sano/peligro",
      "grupo cuya clase ganadora sea atencion",
      "confianza promedio < 0.60",
      "menos de 3 imagenes utiles",
      "captura borrosa o evidencia insuficiente"
    ],
    "can_skip_gemini_only_if": [
      "modelo local aprobado en fase 5",
      ">= 3 imagenes utiles del grupo",
      "confianza promedio >= 0.80",
      "voto consistente entre imagenes",
      "sin contradiccion sano/peligro"
    ],
    "current_project_status": {
      "modelo_local_aprobado_fase5": false,
      "gemini_skip_allowed_for_final_diagnosis": false,
      "reason": "Fase 5 no aprobo ningun modelo para diagnostico final."
    }
  },
  "group_decision_input": {
    "groupKey": "PLA_<planta>_MA_<maceta>_<lado>",
    "plantId": "number|null",
    "potId": "number|null",
    "side": "D|I|O|null",
    "images": [
      {
        "imageId": "string",
        "mimeType": "image/jpeg",
        "imagenBase64": "...",
        "localPrediction": {
          "estado": "SANO|ATENCION|PELIGRO",
          "confianza": 0.0,
          "bucket": "alta|media|baja"
        }
      }
    ]
  },
  "group_decision_output": {
    "localEstadoPreliminar": "SANO|ATENCION|PELIGRO|AMBIGUO",
    "localConfianzaPromedio": 0.0,
    "accion": "USAR_GEMINI|CAPTURA_ADICIONAL|REVISION_MANUAL|SOLO_PRELIMINAR",
    "geminiRequired": true,
    "selectedImageIdsForGemini": [],
    "motivosEscalamiento": []
  },
  "phase6_reference": {
    "thresholds": {
      "high": 0.8,
      "mid": 0.6
    },
    "final_diagnosis_allowed": false,
    "bucket_stats": [
      {
        "bucket": "alta",
        "threshold": "confianza >= 0.80",
        "total": 270,
        "correct": 222,
        "accuracy": 0.8222222222222222
      },
      {
        "bucket": "media",
        "threshold": "0.60 <= confianza < 0.80",
        "total": 228,
        "correct": 158,
        "accuracy": 0.6929824561403509
      },
      {
        "bucket": "baja",
        "threshold": "confianza < 0.60",
        "total": 162,
        "correct": 86,
        "accuracy": 0.5308641975308642
      }
    ]
  }
}
```

## Cambios sugeridos para una fase posterior de backend

- Agregar endpoint `POST /api/analisis/grupo`.
- Aceptar multiples imagenes con `groupKey`, `plantId`, `potId`, `side` y predicciones locales.
- Seleccionar 1 a 3 imagenes para Gemini segun peligro, baja confianza o contradiccion.
- Persistir resultado local preliminar y resultado Gemini final por separado.
- Mantener `POST /api/analisis/planta` para analisis manual/individual.

## Salida operativa

El reporte final debe distinguir:

- `localEstadoPreliminar`: resultado rapido del modelo local.
- `geminiEstadoFinal`: resultado final cuando se escale.
- `requiereRevisionManual`: true si hay ambiguedad o evidencia insuficiente.
- `motivosEscalamiento`: lista concreta de razones.
