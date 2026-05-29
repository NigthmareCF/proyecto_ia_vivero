# Fase 4: entrenamiento comparativo modelo IA local

Fecha: 2026-05-28 06:24:13
Dataset: `C:\Proyecto_IA_Vivero\dataset_curado`

## Resultado

Mejor candidato entrenado: `mobilenetv2`
Accuracy test candidato: `63.51%`
Macro F1 candidato: `0.6172`
Mejor resultado general medido: `baseline_modelo_vivero_tflite` con `68.47%`.
Aceptado como reemplazo del modelo actual: `no`.
TFLite candidato: `C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_comparativo\mobilenetv2\mobilenetv2.tflite`

## Comparacion

| Modelo | Accuracy test | Macro F1 | atencion | peligro | sano |
|---|---:|---:|---:|---:|---:|
| baseline_modelo_vivero_tflite | 68.47% | 0.6754 | 47.30% | 74.32% | 83.78% |
| mobilenetv2 | 63.51% | 0.6172 | 33.78% | 78.38% | 78.38% |
| mobilenetv3small | 61.26% | 0.6104 | 51.35% | 74.32% | 58.11% |
| efficientnetv2b0 | 59.46% | 0.5875 | 41.89% | 64.86% | 71.62% |

## Archivos generados

- `modelos/modelo_vivero_v2.keras`
- `modelos/modelo_vivero_v2.tflite`
- `modelos/labels.txt`
- `training/fase4_entrenamiento_comparativo/metrics_modelo_v2.json`
- `training/fase4_entrenamiento_comparativo/confusion_matrix_modelo_v2.csv`

## Decision

El candidato se exporta como `modelo_vivero_v2`, pero no debe integrarse al backend si `accepted_as_replacement` es `false` en `metrics_modelo_v2.json`.
