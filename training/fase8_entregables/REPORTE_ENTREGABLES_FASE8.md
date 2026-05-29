# Fase 8: entregables finales del plan IA local

Fecha: 2026-05-28 23:23:13

## Estado final

- Dataset curado: `2190` imagenes en train/validation/test.
- Imagenes en revision/dudosas: `1120`.
- Mejor modelo medido: `baseline_modelo_vivero_tflite` con `68.47%`.
- Mejor candidato entrenado: `mobilenetv2` con `63.51%`.
- `modelo_vivero_v2` aceptado como reemplazo: `no`.
- Aprobado para diagnostico final: `no`.

## Entregables esperados

| Ruta | Existe | Tipo | Archivos | Tamano bytes |
|---|---|---|---:|---:|
| `modelos/modelo_vivero_v2.keras` | si | file | 1 | 9680608 |
| `modelos/modelo_vivero_v2.tflite` | si | file | 1 | 4518612 |
| `modelos/labels.txt` | si | file | 1 | 25 |
| `training/reporte_modelo_v2.md` | si | file | 1 | 1337 |
| `training/metrics_modelo_v2.json` | si | file | 1 | 9725 |
| `training/confusion_matrix_modelo_v2.csv` | si | file | 1 | 86 |
| `dataset_curado` | si | directory | 3313 | 87112802 |

## Reportes por fase

- `training/auditoria_fase1_20260528_043608/REPORTE_AUDITORIA_FASE1.md`
- `training/fase2_reglas_etiquetado/REGLAS_ETIQUETADO_FASE2.md`
- `dataset_curado/REPORTE_FASE3_DATASET_CURADO.md`
- `training/reporte_modelo_v2.md`
- `training/fase5_criterio_aceptacion/REPORTE_CRITERIO_ACEPTACION_FASE5.md`
- `training/fase6_decision_confianza/REPORTE_DECISION_CONFIANZA_FASE6.md`
- `training/fase7_flujo_gemini/REPORTE_FLUJO_GEMINI_FASE7.md`

## Decision de integracion

No integrar `modelos/modelo_vivero_v2.tflite` al backend como reemplazo del modelo actual. El archivo existe como candidato entrenado y evidencia de fase 4, pero no supero el baseline ni el criterio minimo de fase 5.

El uso correcto del modelo local por ahora es filtro rapido por grupo, con escalamiento a Gemini o revision manual segun fase 6 y fase 7.

## Pendientes tecnicos

- Revisar manualmente `dataset_curado/revision_dudosa` para recuperar ejemplos utiles.
- Conseguir mas datos reales de `atencion` con sintomas claros y balanceados.
- Reentrenar con mas datos o estrategia especifica para `atencion` antes de intentar reemplazo.
- Implementar en backend solo despues un flujo por grupo `POST /api/analisis/grupo` si se decide avanzar.
