# Auditoria fase 1 del dataset IA local

Fecha: 2026-05-28 04:53:02
Dataset: `C:\Proyecto_IA_Vivero\dataset_curado`
Total de imagenes indexadas: `2190`
Tiempo de auditoria: `45.9` segundos

## Conteo por split y clase

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| raw | 0 | 0 | 0 | 0 |
| train | 510 | 510 | 510 | 1530 |
| validation | 146 | 146 | 146 | 438 |
| test | 74 | 74 | 74 | 222 |

## Hallazgos automaticos

- Imagenes corruptas o ilegibles: `0`.
- Grupos de duplicados exactos por SHA-256: `0`.
- Grupos de duplicados exactos que cruzan `train/validation/test`: `0`.
- Pares perceptualmente similares reportados: `0`.
- Pares perceptualmente similares entre splits: `0`.
- Pares perceptualmente similares entre `train/validation/test`: `0`.
- Pares perceptualmente similares entre clases: `0`.

## Muestra de errores del modelo actual

- Predicciones revisadas en validation/test: `660`.
- Accuracy observado en esta corrida: `70.61%`.
- Imagenes reales `atencion` evaluadas: `220`.
- Errores donde la clase real era `atencion`: `96`.
- Grilla visual: `muestra_errores_atencion.jpg` si hubo errores aplicables.

### Accuracy por clase

| Clase real | Imagenes | Correctas | Accuracy |
|---|---:|---:|---:|
| atencion | 220 | 124 | 56.36% |
| peligro | 220 | 160 | 72.73% |
| sano | 220 | 182 | 82.73% |

### Matriz de confusion

| Real \ Predicha | atencion | peligro | sano |
|---|---:|---:|---:|
| atencion | 124 | 53 | 43 |
| peligro | 26 | 160 | 34 |
| sano | 20 | 18 | 182 |

## Archivos generados

- `records.csv`: inventario completo de imagenes auditadas.
- `counts.json`: conteos por split y clase.
- `corrupt_images.csv`: imagenes ilegibles o corruptas.
- `exact_duplicates.csv`: grupos con bytes identicos.
- `perceptual_similar_pairs.csv`: pares casi iguales detectados por pHash.
- `predictions_validation_test.csv`: predicciones del modelo actual sobre validation/test.

## Lectura inicial

Esta auditoria inicia la fase 1 sin modificar el dataset. Los pasos manuales siguientes son revisar `perceptual_similar_pairs.csv` para decidir si hay fuga real entre train/validation/test y revisar visualmente `muestra_errores_atencion.jpg` para separar `atencion` leve, severo y casi sano antes de construir `dataset_curado`.
