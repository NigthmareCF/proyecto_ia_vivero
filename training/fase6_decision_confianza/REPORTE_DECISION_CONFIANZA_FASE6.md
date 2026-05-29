# Fase 6: decision por confianza

Fecha: 2026-05-28 06:30:06
Predicciones base: `C:\Proyecto_IA_Vivero\training\auditoria_fase3_dataset_curado\predictions_validation_test.csv`
Dictamen fase 5: `C:\Proyecto_IA_Vivero\training\fase5_criterio_aceptacion\criterio_aceptacion_fase5.json`

## Decision base

- Modelo aprobado para diagnostico final: `no`.
- Por lo tanto, una confianza alta no significa diagnostico final; significa senal local preliminar.

## Umbrales por imagen

| Bucket | Regla | Imagenes | Correctas | Accuracy observado | Accion |
|---|---|---:|---:|---:|---|
| alta | confianza >= 0.80 | 270 | 222 | 82.22% | preliminar alta; confirmar si afecta decision final |
| media | 0.60 <= confianza < 0.80 | 228 | 158 | 69.30% | agregar con otras imagenes del grupo |
| baja | confianza < 0.60 | 162 | 86 | 53.09% | captura adicional, revision o Gemini |

## Reglas operativas

1. No usar `argmax` solo como diagnostico final.
2. Si `confianza >= 0.80`, aceptar solo como clasificacion preliminar local.
3. Si predice `peligro` con confianza alta, levantar alerta preliminar y confirmar con Gemini/revision.
4. Si `0.60 <= confianza < 0.80`, esperar mas imagenes del mismo grupo.
5. Si `confianza < 0.60`, pedir captura adicional, revision manual o Gemini.
6. Si el grupo mezcla `sano` y `peligro`, escalar aunque haya confianza alta en una imagen.
7. Si la clase ganadora es `atencion`, escalar o pedir mas evidencia porque fue la clase debil en fases 4 y 5.

## Regla por grupo

Grupo operativo: `planta + maceta + lado`.

- Minimo: 3 imagenes.
- Recomendado: 5 imagenes.
- Agregacion: promedio de probabilidades y voto por clase.
- Salida local: `sano_preliminar`, `atencion_preliminar`, `peligro_preliminar`, `ambiguo`, `requiere_gemini`.

## Contrato recomendado para backend

```json
{
  "group_key": "planta + maceta + lado",
  "minimum_images": 3,
  "recommended_images": 5,
  "local_acceptance": {
    "all_required": [
      "modelo_aprobado_en_fase5 == true",
      ">= 3 imagenes del grupo",
      "clase ganadora por promedio/voto",
      "confianza_promedio >= 0.80",
      "sin contradiccion fuerte entre sano y peligro"
    ]
  },
  "current_project_decision": {
    "modelo_aprobado_en_fase5": false,
    "local_final_diagnosis_allowed": false,
    "local_role": "filtro_rapido_para_priorizar_y_decidir_escalamiento"
  },
  "escalation_rules": [
    "Si aparece peligro con confianza alta, generar alerta preliminar y confirmar con Gemini o revision.",
    "Si las imagenes del grupo mezclan sano y peligro, no decidir localmente.",
    "Si la mayoria cae en atencion, pedir confirmacion porque es la clase debil.",
    "Si confianza promedio < 0.60, solicitar captura adicional o revision manual."
  ]
}
```

## Implicacion para fase 7

La fase 7 debe usar Gemini solo cuando el grupo sea ambiguo, haya peligro preliminar, la clase sea atencion o la confianza agregada no sea suficiente.
