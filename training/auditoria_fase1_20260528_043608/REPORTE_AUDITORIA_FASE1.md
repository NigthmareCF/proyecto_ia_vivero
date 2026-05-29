# Auditoria fase 1 del dataset IA local

Fecha: 2026-05-28 04:37:09
Dataset: `C:\Proyecto_IA_Vivero\dataset`
Total de imagenes indexadas: `7024`
Tiempo de auditoria: `61.2` segundos

## Conteo por split y clase

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| raw | 867 | 1213 | 1230 | 3310 |
| train | 804 | 887 | 907 | 2598 |
| validation | 229 | 253 | 259 | 741 |
| test | 116 | 128 | 131 | 375 |

## Hallazgos automaticos

- Imagenes corruptas o ilegibles: `0`.
- Grupos de duplicados exactos por SHA-256: `2381`.
- Grupos de duplicados exactos que cruzan `train/validation/test`: `48`.
- Pares perceptualmente similares reportados: `3151`.
- Pares perceptualmente similares entre splits: `2880`.
- Pares perceptualmente similares entre `train/validation/test`: `71`.
- Pares perceptualmente similares entre clases: `652`.

## Muestra de errores del modelo actual

- Predicciones revisadas en validation/test: `1116`.
- Accuracy observado en esta corrida: `66.04%`.
- Imagenes reales `atencion` evaluadas: `345`.
- Errores donde la clase real era `atencion`: `183`.
- Grilla visual: `muestra_errores_atencion.jpg` si hubo errores aplicables.

### Accuracy por clase

| Clase real | Imagenes | Correctas | Accuracy |
|---|---:|---:|---:|
| atencion | 345 | 162 | 46.96% |
| peligro | 381 | 274 | 71.92% |
| sano | 390 | 301 | 77.18% |

### Matriz de confusion

| Real \ Predicha | atencion | peligro | sano |
|---|---:|---:|---:|
| atencion | 162 | 85 | 98 |
| peligro | 52 | 274 | 55 |
| sano | 52 | 37 | 301 |

## Archivos generados

- `records.csv`: inventario completo de imagenes auditadas.
- `counts.json`: conteos por split y clase.
- `corrupt_images.csv`: imagenes ilegibles o corruptas.
- `exact_duplicates.csv`: grupos con bytes identicos.
- `perceptual_similar_pairs.csv`: pares casi iguales detectados por pHash.
- `predictions_validation_test.csv`: predicciones del modelo actual sobre validation/test.

## Lectura inicial

Esta auditoria inicia la fase 1 sin modificar el dataset. Los pasos manuales siguientes son revisar `perceptual_similar_pairs.csv` para decidir si hay fuga real entre train/validation/test y revisar visualmente `muestra_errores_atencion.jpg` para separar `atencion` leve, severo y casi sano antes de construir `dataset_curado`.
