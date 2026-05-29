# Recuperacion conservadora de revision_dudosa

Fecha: 2026-05-29 00:32:42
Salida: `C:\Proyecto_IA_Vivero\dataset_curado_v2`

## Criterio

- Se uso el baseline `modelos/modelo_vivero.tflite` como filtro.
- Solo se recuperaron candidatos `atencion` si el baseline predijo `atencion` con confianza alta.
- Se recuperaron excedentes de `peligro` y `sano` solo para mantener balance.
- No se modifico `dataset_curado` original.

## Conteo

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| train | 512 | 512 | 512 | 1536 |
| validation | 146 | 146 | 146 | 438 |
| test | 75 | 75 | 75 | 225 |

## Recuperacion

- Candidatos `atencion` de alta confianza encontrados: `3`.
- Imagenes recuperadas totales: `9`.

| Motivo | Imagenes |
|---|---:|
| duplicado exacto con etiqueta conflictiva | 2 |
| excedente por balance recuperado para mantener balance | 6 |
| similaridad perceptual con etiqueta conflictiva | 1 |

## Advertencia

Este dataset v2 sigue necesitando validacion con entrenamiento. Recuperar ejemplos por confianza mejora cobertura de `atencion`, pero no demuestra por si solo que el modelo vaya a superar el minimo.
