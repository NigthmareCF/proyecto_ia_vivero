# Cierre automatico de revision visual del modelo IA local

Fecha: 2026-05-29

## Objetivo

Continuar el trabajo manual pendiente del plan de mejora del modelo IA local, especialmente la recuperacion de imagenes utiles desde `dataset_curado/revision_dudosa` para reforzar la clase `atencion`.

## Trabajo ejecutado

1. Se reviso `dataset_curado/revision_dudosa`.
   - `conflict_label/atencion`: 137 imagenes.
   - `conflict_label/peligro`: 140 imagenes.
   - `conflict_label/sano`: 97 imagenes.
   - `excedente_balance/peligro`: 343 imagenes.
   - `excedente_balance/sano`: 403 imagenes.

2. Se intento una recuperacion automatica estricta.
   - Script: `training/recuperar_revision_dudosa_atencion.py`.
   - Salida: `dataset_curado_v2`.
   - Resultado: solo 3 candidatas `atencion` con confianza alta del modelo actual.
   - Conclusion: la recuperacion automatica estricta no aporta suficiente volumen.

3. Se genero una revision visual por lotes.
   - Script: `training/generar_lotes_revision_visual.py`.
   - Carpeta: `training/revision_visual_atencion`.
   - Lotes visuales: `atencion_conflicto_lote_01.jpg` a `atencion_conflicto_lote_06.jpg`.
   - Seleccion final: `training/revision_visual_atencion/seleccion_atencion_visual.csv`.
   - Resultado: 70 imagenes seleccionadas visualmente como candidatas `atencion`.

4. Se construyo `dataset_curado_v3`.
   - Script: `training/crear_dataset_curado_v3_visual.py`.
   - Dataset base: `dataset_curado`.
   - Dataset nuevo: `dataset_curado_v3`.
   - Imagenes agregadas totales: 210.
   - Imagenes `atencion` recuperadas: 70.
   - Balance agregado: se agregaron tambien imagenes `peligro` y `sano` desde excedentes para mantener balance.

## Estado de `dataset_curado_v3`

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| train | 559 | 559 | 559 | 1677 |
| validation | 160 | 160 | 160 | 480 |
| test | 81 | 81 | 81 | 243 |

Total: 2400 imagenes.

## Auditoria de `dataset_curado_v3`

Auditoria: `training/auditoria_dataset_curado_v3/REPORTE_AUDITORIA_FASE1.md`.

Resultado tecnico:

- Imagenes corruptas: 0.
- Duplicados exactos: 0.
- Duplicados exactos cruzando splits: 0.
- Pares perceptualmente similares pHash: 0.
- Pares perceptualmente similares entre clases: 0.

Evaluacion del modelo actual sobre validation/test de `dataset_curado_v3`:

| Clase real | Imagenes | Correctas | Accuracy |
|---|---:|---:|---:|
| atencion | 241 | 128 | 53.11% |
| peligro | 241 | 174 | 72.20% |
| sano | 241 | 195 | 80.91% |

Accuracy global validation/test: 68.74%.

Conclusion: el dataset v3 esta limpio tecnicamente, pero el modelo actual no mejora sobre este conjunto frente a la auditoria anterior de `dataset_curado`.

## Entrenamiento exploratorio v3

Se intento entrenar `mobilenetv3small` sobre `dataset_curado_v3`.

- Script usado: `training/entrenar_fase4_comparativo.py`.
- Carpeta: `training/fase4_entrenamiento_v3_visual`.
- Checkpoint generado: `training/fase4_entrenamiento_v3_visual/mobilenetv3small/mobilenetv3small.best.keras`.
- Error final del entrenamiento: `OSError: [Errno 22] Invalid argument`.
- No se genero TFLite final desde ese intento.

Para no perder el checkpoint, se evaluo directamente:

- Script: `training/evaluar_checkpoint_v3_visual.py`.
- Reporte: `training/fase4_entrenamiento_v3_visual/evaluacion_checkpoint/REPORTE_CHECKPOINT_V3_VISUAL.md`.

Resultado del checkpoint:

| Clase real | Recall | Precision | F1 |
|---|---:|---:|---:|
| atencion | 37.04% | 65.22% | 0.4724 |
| peligro | 71.60% | 54.21% | 0.6170 |
| sano | 70.37% | 63.33% | 0.6667 |

Accuracy test: 59.67%.
Macro F1: 0.5854.

Conclusion: este checkpoint queda descartado. No debe sustituir `modelos/modelo_vivero.tflite`.

## Decision actual

No hay modelo nuevo aceptado.

El modelo productivo actual debe mantenerse. Los candidatos `modelo_vivero_v2` y el checkpoint v3 visual no cumplen los criterios de aceptacion definidos en fase 5.

El flujo correcto sigue siendo:

- Modelo local: solo apoyo preliminar y clasificacion de confianza.
- Gemini/backend: diagnostico final.
- No integrar ningun modelo local nuevo como diagnostico definitivo hasta superar criterios minimos.

## Que falta realmente

1. Revisar manualmente mas imagenes de `revision_dudosa`, pero con criterios mas estrictos:
   - separar `atencion leve`;
   - separar `peligro real`;
   - descartar hojas sanas con sombras, brillo o encuadres confusos.

2. Conseguir mas imagenes nuevas de `atencion` con sintomas claros.
   - La clase `atencion` sigue siendo el cuello de botella.
   - Las imagenes conflictivas recuperadas no fueron suficientes para mejorar entrenamiento.

3. Probar entrenamiento con congelamiento y epochs mas conservadores.
   - El intento v3 con MobileNetV3Small bajo demasiado el recall de `atencion`.
   - Antes de otro entrenamiento largo, conviene ajustar hiperparametros o revisar etiquetas.

4. Mantener el criterio de aceptacion:
   - accuracy global minimo: 80%.
   - recall `atencion` minimo: 70%.
   - recall `peligro` minimo: 80%.

5. No tocar backend productivo por ahora.
   - El endpoint real actual sigue siendo `POST /api/analisis/planta`.
   - La propuesta de grupo por `planta + maceta + lado` queda como mejora futura, no como requisito para este cierre.

## Archivos principales creados en esta continuacion

- `training/recuperar_revision_dudosa_atencion.py`
- `dataset_curado_v2/`
- `training/generar_lotes_revision_visual.py`
- `training/revision_visual_atencion/`
- `training/crear_dataset_curado_v3_visual.py`
- `dataset_curado_v3/`
- `training/auditoria_dataset_curado_v3/`
- `training/fase4_entrenamiento_v3_visual/`
- `training/evaluar_checkpoint_v3_visual.py`

