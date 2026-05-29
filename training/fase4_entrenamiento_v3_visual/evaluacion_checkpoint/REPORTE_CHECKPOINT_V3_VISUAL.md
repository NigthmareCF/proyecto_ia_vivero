# Evaluacion checkpoint v3 visual

Fecha: 2026-05-29T01:56:35
Dataset: `C:\Proyecto_IA_Vivero\dataset_curado_v3`
Checkpoint: `C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v3_visual\mobilenetv3small\mobilenetv3small.best.keras`

## Resultado

Accuracy test: `59.67%`
Macro F1: `0.5854`

| Clase real | Recall | Precision | F1 |
|---|---:|---:|---:|
| atencion | 37.04% | 65.22% | 0.4724 |
| peligro | 71.60% | 54.21% | 0.6170 |
| sano | 70.37% | 63.33% | 0.6667 |

## Decision

Este checkpoint no se exporto a TFLite por el fallo del entrenamiento original. No debe sustituir el modelo productivo sin una exportacion TFLite exitosa y sin pasar fase 5.
