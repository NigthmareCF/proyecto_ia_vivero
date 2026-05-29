# Fase 2: reglas de etiquetado para dataset IA local

Fecha: 2026-05-28 04:46:18
Auditoria base: `C:\Proyecto_IA_Vivero\training\auditoria_fase1_20260528_043608`
Salida de revision: `training/fase2_reglas_etiquetado/revision_etiquetado_fase2.csv`

## Objetivo

Hacer consistentes las clases `sano`, `atencion` y `peligro` antes de crear `dataset_curado`.
Esta fase no mueve ni borra imagenes. Solo define reglas y deja una cola de revision.

## Regla principal

Etiqueta por lo que se ve en la planta, no por lo que el nombre del archivo o el split dicen.
Si la imagen no permite decidir con claridad, no debe forzarse a una clase fuerte: va a
`revision_dudosa` en la fase 3.

## Clases

### sano

Usar `sano` cuando la planta se vea funcionalmente normal:

- hojas verdes o con variacion leve natural;
- sin manchas relevantes, necrosis, plaga visible ni marchitez marcada;
- bordes secos minimos o ruido visual que no compromete el estado general;
- fondo, iluminacion o encuadre no deben crear una falsa alarma.

No usar `sano` si hay amarillamiento extendido, manchas multiples, hojas caidas, tejido muerto,
plaga visible o deterioro que un operador deberia revisar.

### atencion

Usar `atencion` para sintomas leves o moderados:

- manchas pequenas o localizadas;
- amarillamiento parcial;
- hojas secas leves o bordes deteriorados;
- estres visible, pero sin dano dominante;
- planta recuperable o caso que requiere seguimiento, no alarma inmediata.

`atencion` es la clase de frontera. Debe excluir dos extremos:

- si casi no hay sintoma visible, mover a `sano`;
- si el dano es extenso, negro, necrotico, con plaga marcada o marchitez fuerte, mover a `peligro`.

### peligro

Usar `peligro` cuando el dano sea fuerte o de riesgo alto:

- necrosis evidente o tejido muerto dominante;
- plaga severa visible;
- marchitez marcada;
- pudricion o manchas oscuras extensas;
- dano que afecta gran parte de la planta;
- caso donde el sistema deberia priorizar alerta o intervencion.

No usar `peligro` para una hoja aislada con borde seco si el resto de la planta luce estable.

## Casos que van a revision_dudosa

Enviar a revision si:

- la imagen esta borrosa, demasiado oscura o demasiado recortada;
- se ve mas maceta/fondo que planta;
- el sintoma podria ser luz/sombra;
- hay mezcla fuerte entre planta sana y una hoja muy danada;
- dos etiquetas parecen igualmente defensibles;
- es duplicado o casi duplicado de otra imagen con etiqueta distinta.

## Reglas para duplicados

1. Si dos archivos son la misma imagen exacta y tienen etiquetas distintas, elegir una sola etiqueta canonica.
2. Si una imagen exacta aparece en `train` y tambien en `validation` o `test`, dejarla solo en un split en fase 3.
3. Si dos imagenes son casi iguales, tratarlas como un mismo grupo visual para evitar fuga entre splits.
4. El `test` curado debe conservar imagenes no vistas por entrenamiento ni validacion.

## Prioridad de revision

La cola de revision contiene `967` entradas:

- Criticas: `132`.
- Altas: `746`.
- Medias: `89`.

Origenes principales:

- Errores del modelo en `atencion`: `183`.
- Duplicados exactos conflictivos o con fuga: `132`.
- Pares similares entre clases: `652`.

## Decision para fase 3

Al construir `dataset_curado`, cada imagen revisada debe caer en una de estas decisiones:

- `keep_sano`
- `keep_atencion`
- `keep_peligro`
- `move_sano`
- `move_atencion`
- `move_peligro`
- `revision_dudosa`
- `excluir_duplicado`
- `excluir_baja_calidad`

La fase 3 debe crear una copia curada. No debe editar `dataset/raw`, `dataset/train`,
`dataset/validation` ni `dataset/test` directamente.
