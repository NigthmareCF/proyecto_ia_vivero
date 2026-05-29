# Fase 3: dataset curado

Fecha: 2026-05-28 04:52:11
Auditoria base: `C:\Proyecto_IA_Vivero\training\auditoria_fase1_20260528_043608`
Salida: `C:\Proyecto_IA_Vivero\dataset_curado`

## Resultado

- Total en `train/validation/test`: `2190` imagenes.
- Total enviado a `revision_dudosa`: `1120` imagenes.
- El dataset original no fue modificado.

## Conteo curado

| Split | atencion | peligro | sano | Total |
|---|---:|---:|---:|---:|
| train | 510 | 510 | 510 | 1530 |
| validation | 146 | 146 | 146 | 438 |
| test | 74 | 74 | 74 | 222 |

## Revision dudosa

| Motivo | Imagenes |
|---|---:|
| duplicado exacto con etiqueta conflictiva | 172 |
| excedente por balance de clases | 746 |
| similaridad perceptual con etiqueta conflictiva | 202 |

## Criterio aplicado

- Se copio desde `dataset/raw`, no desde los splits anteriores.
- Se excluyeron de entrenamiento imagenes con duplicado exacto entre etiquetas distintas.
- Se excluyeron de entrenamiento imagenes con similitud perceptual contra otra clase.
- Se elimino duplicado exacto dentro de una misma clase conservando una copia canonica.
- Se balancearon las tres clases al tamano de la clase usable mas pequena.
- Los excedentes por balance quedaron en `revision_dudosa/excedente_balance` para no perder trazabilidad.

## Siguiente paso

La fase 4 debe entrenar contra `dataset_curado` y comparar el resultado con el modelo actual.
