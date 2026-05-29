# Auditoria fase 1 del dataset IA local

Fecha: 2026-05-29 00:38:52
Dataset: `C:\Proyecto_IA_Vivero\dataset_curado_v3`
Total de imagenes indexadas: `2400`
Tiempo de auditoria: `93.6` segundos

## Conteo por split y clase

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| raw | 0 | 0 | 0 | 0 |
| train | 559 | 559 | 559 | 1677 |
| validation | 160 | 160 | 160 | 480 |
| test | 81 | 81 | 81 | 243 |

## Hallazgos automaticos

- Imagenes corruptas o ilegibles: `0`.
- Grupos de duplicados exactos por SHA-256: `0`.
- Grupos de duplicados exactos que cruzan `train/validation/test`: `0`.
- Pares perceptualmente similares reportados: `0`.
- Pares perceptualmente similares entre splits: `0`.
- Pares perceptualmente similares entre `train/validation/test`: `0`.
- Pares perceptualmente similares entre clases: `0`.

## Muestra de errores del modelo actual

- Predicciones revisadas en validation/test: `723`.
- Accuracy observado en esta corrida: `68.74%`.
- Imagenes reales `atencion` evaluadas: `241`.
- Errores donde la clase real era `atencion`: `113`.
- Grilla visual: `muestra_errores_atencion.jpg` si hubo errores aplicables.

### Accuracy por clase

| Clase real | Imagenes | Correctas | Accuracy |
|---|---:|---:|---:|
| atencion | 241 | 128 | 53.11% |
| peligro | 241 | 174 | 72.20% |
| sano | 241 | 195 | 80.91% |

### Matriz de confusion

| Real \ Predicha | atencion | peligro | sano |
|---|---:|---:|---:|
| atencion | 128 | 66 | 47 |
| peligro | 28 | 174 | 39 |
| sano | 24 | 22 | 195 |

## Archivos generados

- `records.csv`: inventario completo de imagenes auditadas.
- `counts.json`: conteos por split y clase.
- `corrupt_images.csv`: imagenes ilegibles o corruptas.
- `exact_duplicates.csv`: grupos con bytes identicos.
- `perceptual_similar_pairs.csv`: pares casi iguales detectados por pHash.
- `predictions_validation_test.csv`: predicciones del modelo actual sobre validation/test.

## Lectura inicial

Esta auditoria inicia la fase 1 sin modificar el dataset. Los pasos manuales siguientes son revisar `perceptual_similar_pairs.csv` para decidir si hay fuga real entre train/validation/test y revisar visualmente `muestra_errores_atencion.jpg` para separar `atencion` leve, severo y casi sano antes de construir `dataset_curado`.
