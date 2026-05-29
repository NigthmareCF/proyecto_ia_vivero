# Handoff ultra detallado para continuar la mejora del modelo IA local

Fecha: 2026-05-29

## Proposito de este documento

Este documento deja instrucciones completas para que otra IA, otro operador o una sesion futura pueda continuar el mejoramiento del modelo IA local sin repetir trabajo ya hecho y sin poner en riesgo el modelo productivo actual.

El punto mas importante es este:

> No hay un modelo nuevo aceptado. El problema principal no es el script de entrenamiento, sino la calidad y separacion visual de la clase `atencion`.

El modelo actual debe mantenerse como modelo productivo hasta que un candidato nuevo supere los criterios de aceptacion definidos.

---

## Superficies del proyecto que NO deben mezclarse

Este trabajo pertenece a la superficie local de dataset/modelo/training dentro de:

`C:\Proyecto_IA_Vivero`

No debe mezclarse con:

- `worktrees/release`
- `worktrees/frontend`
- `worktrees/robot-pi`
- backend productivo
- frontend productivo
- runtime del robot

La mejora del modelo local debe avanzar primero como trabajo de datos, auditoria y entrenamiento. Solo cuando exista un candidato aceptado se debe hablar de integracion.

---

## Estado final confirmado antes de este handoff

### Dataset original auditado

Dataset auditado:

`dataset`

Reporte:

`training/auditoria_fase1_20260528_043608/REPORTE_AUDITORIA_FASE1.md`

Hallazgos principales:

- Imagenes totales: 7024.
- Imagenes corruptas: 0.
- Grupos de duplicados exactos: 2381.
- Grupos exactos cruzando `train/validation/test`: 48.
- Pares perceptuales similares cruzando splits: 71.
- Accuracy del modelo actual en esa auditoria: 66.04%.
- Accuracy/recall observado para `atencion`: 46.96%.

Conclusion:

El dataset original no es confiable para entrenamiento directo porque tiene mucha duplicacion y posible fuga entre splits.

---

## Dataset curado base

Dataset:

`dataset_curado`

Reporte:

`dataset_curado/REPORTE_FASE3_DATASET_CURADO.md`

Auditoria:

`training/auditoria_fase3_dataset_curado/REPORTE_AUDITORIA_FASE1.md`

Conteo:

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| train | 510 | 510 | 510 | 1530 |
| validation | 146 | 146 | 146 | 438 |
| test | 74 | 74 | 74 | 222 |

Total usable:

`2190`

Revision dudosa:

`1120`

Resultado de auditoria:

- Imagenes corruptas: 0.
- Duplicados exactos: 0.
- Pares perceptuales similares: 0.
- Accuracy del modelo actual sobre validation/test: 70.61%.
- `atencion`: 56.36%.

Conclusion:

`dataset_curado` es el mejor dataset estable hasta ahora. Es limpio tecnicamente, pero todavia insuficiente para un modelo aceptable.

---

## Dataset curado v2

Dataset:

`dataset_curado_v2`

Script:

`training/recuperar_revision_dudosa_atencion.py`

Objetivo:

Recuperar automaticamente imagenes de `atencion` desde `revision_dudosa` usando el modelo actual como filtro estricto.

Criterio usado:

- Solo recuperar imagenes de revision dudosa donde el modelo actual predice `atencion`.
- Confianza minima: 0.80.
- Balancear con imagenes de `peligro` y `sano`.

Resultado:

- Solo se recuperaron 3 candidatas `atencion`.
- Se agregaron 9 imagenes totales contando balance.

Conteo:

| Split | atencion | peligro | sano |
|---|---:|---:|---:|
| train | 512 | 512 | 512 |
| validation | 146 | 146 | 146 |
| test | 75 | 75 | 75 |

Conclusion:

La recuperacion automatica estricta no aporta suficiente volumen. No debe considerarse una mejora real.

---

## Revision visual de `atencion`

Carpeta:

`training/revision_visual_atencion`

Script generador:

`training/generar_lotes_revision_visual.py`

Archivos visuales generados:

- `atencion_conflicto_lote_01.jpg`
- `atencion_conflicto_lote_02.jpg`
- `atencion_conflicto_lote_03.jpg`
- `atencion_conflicto_lote_04.jpg`
- `atencion_conflicto_lote_05.jpg`
- `atencion_conflicto_lote_06.jpg`

CSV de seleccion:

`training/revision_visual_atencion/seleccion_atencion_visual.csv`

Resultado:

- Se seleccionaron visualmente 70 imagenes como candidatas `atencion`.

Advertencia:

Esta seleccion fue una recuperacion visual asistida, no una validacion biologica perfecta. Sirve como experimento, no como verdad definitiva.

---

## Dataset curado v3

Dataset:

`dataset_curado_v3`

Script:

`training/crear_dataset_curado_v3_visual.py`

Reporte:

`dataset_curado_v3/REPORTE_DATASET_CURADO_V3_VISUAL.md`

Manifest:

`dataset_curado_v3/MANIFEST_DATASET_CURADO_V3.json`

Imagenes agregadas:

- `atencion`: 70.
- `peligro` + `sano` para balance: 140.
- Total agregado: 210.

Conteo:

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| train | 559 | 559 | 559 | 1677 |
| validation | 160 | 160 | 160 | 480 |
| test | 81 | 81 | 81 | 243 |

Total:

`2400`

---

## Auditoria de dataset_curado_v3

Auditoria:

`training/auditoria_dataset_curado_v3/REPORTE_AUDITORIA_FASE1.md`

Resultado tecnico:

- Imagenes auditadas: 2400.
- Corruptas/ilegibles: 0.
- Duplicados exactos: 0.
- Duplicados exactos cruzando splits: 0.
- Pares similares pHash: 0.
- Pares perceptualmente similares entre clases: 0.

Resultado del modelo actual sobre validation/test:

| Clase real | Imagenes | Correctas | Accuracy |
|---|---:|---:|---:|
| atencion | 241 | 128 | 53.11% |
| peligro | 241 | 174 | 72.20% |
| sano | 241 | 195 | 80.91% |

Accuracy global:

`68.74%`

Conclusion:

`dataset_curado_v3` esta limpio tecnicamente, pero el modelo actual no mejora al evaluarse sobre ese conjunto. La recuperacion visual agrego volumen, pero tambien agrego dificultad o ambiguedad.

---

## Entrenamiento exploratorio sobre dataset_curado_v3

Script usado:

`training/entrenar_fase4_comparativo.py`

Comando usado:

```powershell
& 'C:\Proyecto_IA_Vivero\.venv-ml\Scripts\python.exe' 'C:\Proyecto_IA_Vivero\training\entrenar_fase4_comparativo.py' --dataset 'C:\Proyecto_IA_Vivero\dataset_curado_v3' --output-dir 'C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v3_visual' --models mobilenetv3small
```

Resultado:

- Se genero checkpoint:
  `training/fase4_entrenamiento_v3_visual/mobilenetv3small/mobilenetv3small.best.keras`
- El entrenamiento termino con:
  `OSError: [Errno 22] Invalid argument`
- No se genero TFLite final.
- No se debe usar este checkpoint como modelo productivo.

Evaluacion posterior del checkpoint:

Script:

`training/evaluar_checkpoint_v3_visual.py`

Reporte:

`training/fase4_entrenamiento_v3_visual/evaluacion_checkpoint/REPORTE_CHECKPOINT_V3_VISUAL.md`

Resultado:

| Clase real | Recall | Precision | F1 |
|---|---:|---:|---:|
| atencion | 37.04% | 65.22% | 0.4724 |
| peligro | 71.60% | 54.21% | 0.6170 |
| sano | 70.37% | 63.33% | 0.6667 |

Accuracy test:

`59.67%`

Macro F1:

`0.5854`

Decision:

Este checkpoint queda descartado.

---

## Modelos y candidatos existentes

Modelo productivo actual:

`modelos/modelo_vivero.tflite`

No reemplazarlo.

Candidato v2:

- `modelos/modelo_vivero_v2.keras`
- `modelos/modelo_vivero_v2.tflite`
- `training/metrics_modelo_v2.json`
- `training/reporte_modelo_v2.md`

Estado:

No aceptado.

Resultados comparativos anteriores:

| Modelo | Accuracy test | atencion | peligro | sano |
|---|---:|---:|---:|---:|
| baseline actual | 68.47% | 47.30% | 74.32% | 83.78% |
| MobileNetV2 v2 | 63.51% | 33.78% | 78.38% | 78.38% |
| MobileNetV3Small | 61.26% | 51.35% | 74.32% | 58.11% |
| EfficientNetV2B0 | 59.46% | 41.89% | 64.86% | 71.62% |

Conclusion:

Ningun candidato supera al modelo actual de forma aceptable. Ninguno debe integrarse.

---

## Criterio de aceptacion obligatorio

Un modelo nuevo solo puede reemplazar al actual si cumple todos estos puntos:

1. Accuracy global minimo:

   `80%`

2. Recall minimo de `atencion`:

   `70%`

3. Recall minimo de `peligro`:

   `80%`

4. Sin duplicados exactos cruzando splits.

5. Sin pares perceptualmente similares cruzando splits.

6. Sin pares perceptualmente similares entre clases.

7. TFLite exportado correctamente.

8. Reporte de matriz de confusion generado.

9. Fase 5 debe marcar `accepted_as_replacement: true`.

Hasta que todo eso se cumpla:

> No tocar `modelos/modelo_vivero.tflite`.

---

## Diagnostico real del problema

El cuello de botella es la clase:

`atencion`

Problemas observados:

1. `atencion` se parece demasiado a `sano` cuando los sintomas son leves.
2. `atencion` se parece demasiado a `peligro` cuando los sintomas ya son severos.
3. Hay imagenes con sombras, brillos, encuadres y fondos que confunden al modelo.
4. Parte de `revision_dudosa` contiene ejemplos visualmente ambiguos.
5. Agregar volumen sin limpiar mejor las fronteras entre clases puede empeorar el entrenamiento.

Por eso `dataset_curado_v3` aumento el volumen pero no mejoro el resultado.

---

## Trabajo que falta hacer

### Fase A: redefinir reglas visuales de clase

Crear o actualizar un documento de reglas de etiquetado donde las clases queden asi:

#### `sano`

Debe incluir:

- Hojas verdes.
- Sin manchas visibles.
- Sin zonas secas.
- Sin amarillamiento marcado.
- Sin dano mecanico fuerte.
- Sin sintomas de plaga claros.

Debe excluir:

- Hojas con manchas dudosas.
- Hojas con puntas secas visibles.
- Hojas amarillentas.
- Hojas con brillo o sombra que parezca sintoma.
- Imagenes borrosas donde no se puede confirmar sanidad.

#### `atencion`

Debe incluir:

- Sintomas leves o moderados.
- Amarillamiento parcial.
- Manchas pequenas o medianas.
- Puntas secas leves.
- Deterioro visible pero no generalizado.
- Planta que todavia puede recuperarse.

Debe excluir:

- Imagenes casi sanas.
- Imagenes con dano severo.
- Hojas destruidas o muy secas.
- Plantas claramente en estado critico.
- Imagenes donde el sintoma sea solo sombra, brillo o desenfoque.

#### `peligro`

Debe incluir:

- Dano severo.
- Necrosis amplia.
- Hojas muy secas.
- Amarillamiento fuerte/generalizado.
- Planta muy deteriorada.
- Riesgo claro de perdida.

Debe excluir:

- Dano leve.
- Una sola hoja pequena con sintoma.
- Casos recuperables que correspondan mejor a `atencion`.

---

### Fase B: revisar `revision_dudosa` de forma mas estricta

Carpeta origen:

`dataset_curado/revision_dudosa`

Prioridad de revision:

1. `dataset_curado/revision_dudosa/conflict_label/atencion`
2. `dataset_curado/revision_dudosa/conflict_label/peligro`
3. `dataset_curado/revision_dudosa/conflict_label/sano`
4. `dataset_curado/revision_dudosa/excedente_balance/peligro`
5. `dataset_curado/revision_dudosa/excedente_balance/sano`

Objetivo:

Construir un CSV manual con decisiones:

```csv
source_path,decision,target_class,confidence,reason,notes
```

Valores permitidos para `decision`:

- `keep`
- `discard`
- `move`

Valores permitidos para `target_class`:

- `atencion`
- `peligro`
- `sano`
- vacio si `decision=discard`

Valores sugeridos para `confidence`:

- `alta`
- `media`
- `baja`

Reglas:

- Solo usar imagenes con `confidence=alta` para entrenamiento.
- Imagenes con `confidence=media` deben quedarse en revision.
- Imagenes con `confidence=baja` deben descartarse.
- Si una imagen parece `atencion` pero podria ser `sano`, no usarla.
- Si una imagen parece `atencion` pero podria ser `peligro`, no usarla.

---

### Fase C: conseguir imagenes nuevas de `atencion`

Este es el paso mas importante.

Meta minima:

- Agregar al menos 300 imagenes nuevas y claras de `atencion`.

Meta recomendada:

- 500 a 800 imagenes nuevas de `atencion`.

Condiciones:

- Deben venir de plantas reales.
- Deben tener sintomas leves o moderados.
- Deben evitar duplicados del mismo encuadre.
- Deben evitar rafagas casi identicas.
- Deben capturar diferentes iluminaciones.
- Deben capturar diferentes fondos.
- Deben capturar distintos angulos.
- Deben mantener el sintoma visible.

No sirve agregar:

- La misma imagen recortada muchas veces.
- Imagenes casi iguales del mismo momento.
- Hojas sanas marcadas como `atencion`.
- Hojas severamente danadas marcadas como `atencion`.

---

### Fase D: crear `dataset_curado_v4`

Cuando existan nuevas imagenes revisadas, crear:

`dataset_curado_v4`

Recomendacion de conteo inicial:

| Split | atencion | peligro | sano |
|---|---:|---:|---:|
| train | 800 | 800 | 800 |
| validation | 200 | 200 | 200 |
| test | 100 | 100 | 100 |

Si no hay suficientes imagenes:

- No forzar balance con imagenes dudosas.
- Es mejor un dataset mas pequeno y limpio que uno grande y ambiguo.

Regla importante:

El split debe hacerse por grupo visual, no solo por archivo. Imagenes del mismo lote, misma planta o misma rafaga no deben cruzar entre train/validation/test.

---

### Fase E: auditar `dataset_curado_v4`

Comando base:

```powershell
& 'C:\Proyecto_IA_Vivero\.venv-ml\Scripts\python.exe' 'C:\Proyecto_IA_Vivero\training\auditar_dataset_fase1.py' --dataset 'C:\Proyecto_IA_Vivero\dataset_curado_v4' --output 'C:\Proyecto_IA_Vivero\training\auditoria_dataset_curado_v4' --phash-limit 10000
```

Requisitos para continuar:

- 0 corruptas.
- 0 duplicados exactos.
- 0 duplicados exactos cruzando splits.
- 0 pares perceptualmente similares cruzando splits.
- 0 pares perceptualmente similares entre clases.

Si falla:

- No entrenar.
- Corregir dataset primero.

---

### Fase F: entrenamiento nuevo

Solo entrenar despues de que `dataset_curado_v4` pase auditoria.

Primer intento recomendado:

```powershell
& 'C:\Proyecto_IA_Vivero\.venv-ml\Scripts\python.exe' 'C:\Proyecto_IA_Vivero\training\entrenar_fase4_comparativo.py' --dataset 'C:\Proyecto_IA_Vivero\dataset_curado_v4' --output-dir 'C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v4' --models mobilenetv2,mobilenetv3small
```

Si la maquina tarda demasiado:

```powershell
& 'C:\Proyecto_IA_Vivero\.venv-ml\Scripts\python.exe' 'C:\Proyecto_IA_Vivero\training\entrenar_fase4_comparativo.py' --dataset 'C:\Proyecto_IA_Vivero\dataset_curado_v4' --output-dir 'C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v4_mobilenetv2' --models mobilenetv2
```

Despues probar:

```powershell
& 'C:\Proyecto_IA_Vivero\.venv-ml\Scripts\python.exe' 'C:\Proyecto_IA_Vivero\training\entrenar_fase4_comparativo.py' --dataset 'C:\Proyecto_IA_Vivero\dataset_curado_v4' --output-dir 'C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v4_mobilenetv3small' --models mobilenetv3small
```

No usar EfficientNetV2B0 primero porque fue mas lento y no mejoro resultados anteriores.

---

### Fase G: aceptacion

Despues del entrenamiento, correr fase 5 sobre el nuevo reporte/metricas si el script queda parametrizado para v4. Si no esta parametrizado, adaptar el script sin cambiar el criterio.

Criterio:

- Accuracy global >= 80%.
- Recall `atencion` >= 70%.
- Recall `peligro` >= 80%.

Si no cumple:

- No integrar.
- Documentar.
- Volver a datos.

Si cumple:

- Guardar reporte.
- Guardar matriz de confusion.
- Guardar TFLite.
- Ejecutar validacion final.
- Recien entonces considerar integracion.

---

## Tareas tecnicas recomendadas antes de otra IA

### 1. Hacer scripts mas parametrizables

Estos scripts existen pero algunos reportes todavia usan nombres de fase anteriores:

- `training/evaluar_fase5_aceptacion.py`
- `training/evaluar_fase6_confianza.py`
- `training/generar_fase8_entregables.py`

Mejora recomendada:

Agregar argumentos:

- `--metrics`
- `--output-dir`
- `--dataset`
- `--model-name`

Objetivo:

Poder evaluar v4 sin sobrescribir ni confundir reportes de v2.

---

### 2. Evitar que entrenamiento sobrescriba candidatos globales automaticamente

El script:

`training/entrenar_fase4_comparativo.py`

Actualmente puede copiar el mejor candidato a:

- `modelos/modelo_vivero_v2.keras`
- `modelos/modelo_vivero_v2.tflite`

Recomendacion:

Agregar bandera:

`--no-promote`

O cambiar comportamiento para que solo copie a `modelos/` cuando:

- el candidato supere al baseline;
- pase criterio de aceptacion;
- se use una bandera explicita `--promote`.

Esto evita confusiones.

---

### 3. Guardar logs de entrenamiento

Cuando se entrena en Windows, la salida puede perderse si hay timeout.

Recomendacion:

Ejecutar asi:

```powershell
& 'C:\Proyecto_IA_Vivero\.venv-ml\Scripts\python.exe' 'C:\Proyecto_IA_Vivero\training\entrenar_fase4_comparativo.py' --dataset 'C:\Proyecto_IA_Vivero\dataset_curado_v4' --output-dir 'C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v4' --models mobilenetv2,mobilenetv3small *> 'C:\Proyecto_IA_Vivero\training\fase4_entrenamiento_v4\training.log'
```

Si la carpeta no existe antes, crearla primero.

---

## Flujo Gemini/backend

Estado actual:

- Endpoint real existente:
  `POST /api/analisis/planta`
- Analisis actual:
  una imagen hacia Gemini.
- No existe todavia endpoint de analisis por grupo.

Conclusion:

Gemini debe seguir siendo diagnostico final.

Mejora futura:

Crear endpoint:

`POST /api/analisis/grupo`

Agrupacion recomendada:

- planta
- maceta
- lado

La idea es que el modelo local pueda sugerir confianza preliminar, pero Gemini consolide diagnostico usando varias imagenes del mismo objetivo.

No hacer esta integracion hasta que el flujo de datos/modelo este estable.

---

## Checklist para la siguiente IA

Antes de hacer cualquier cambio:

- [ ] Leer este documento completo.
- [ ] Leer `documentacion_local_raiz/mods/CIERRE_AUTO_REVISION_VISUAL_MODELO_IA_2026-05-29.md`.
- [ ] Revisar `training/metrics_modelo_v2.json`.
- [ ] Revisar `training/auditoria_dataset_curado_v3/REPORTE_AUDITORIA_FASE1.md`.
- [ ] Confirmar que no se va a reemplazar `modelos/modelo_vivero.tflite`.

Trabajo de datos:

- [ ] Crear reglas visuales finales para `sano`, `atencion`, `peligro`.
- [ ] Revisar manualmente mas imagenes de `revision_dudosa`.
- [ ] Crear CSV de decisiones manuales.
- [ ] Conseguir nuevas imagenes claras de `atencion`.
- [ ] Construir `dataset_curado_v4`.
- [ ] Auditar `dataset_curado_v4`.

Trabajo de entrenamiento:

- [ ] Entrenar solo si v4 pasa auditoria.
- [ ] Comparar contra baseline.
- [ ] Evaluar por clase.
- [ ] Revisar matriz de confusion.
- [ ] Exportar TFLite solo si el candidato vale la pena.
- [ ] Correr fase 5.

Trabajo de integracion:

- [ ] No tocar backend si no hay modelo aceptado.
- [ ] No tocar frontend si no hay modelo aceptado.
- [ ] Mantener Gemini como diagnostico final.

---

## Decision final de este handoff

El siguiente trabajo no debe ser "entrenar otra vez" inmediatamente.

La siguiente accion correcta es:

> mejorar datos y etiquetas de `atencion`, construir `dataset_curado_v4`, auditarlo y solo despues reentrenar.

Mientras tanto:

> conservar el modelo actual y no integrar candidatos nuevos.

