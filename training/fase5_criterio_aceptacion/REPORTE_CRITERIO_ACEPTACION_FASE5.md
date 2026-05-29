# Fase 5: criterio de aceptacion modelo IA local

Fecha: 2026-05-28 06:28:12
Metricas base: `C:\Proyecto_IA_Vivero\training\metrics_modelo_v2.json`

## Criterio

| Nivel | Accuracy test | atencion | peligro |
|---|---:|---:|---:|
| Minimo | 80.00% | 70.00% | 80.00% |
| Ideal | 85.00% | 80.00% | 85.00% |

## Resultado por modelo

| Modelo | Accuracy | atencion | peligro | sano | Macro F1 | Minimo | Ideal |
|---|---:|---:|---:|---:|---:|---|---|
| baseline_modelo_vivero_tflite | 68.47% | 47.30% | 74.32% | 83.78% | 0.6754 | FAIL | FAIL |
| mobilenetv2 | 63.51% | 33.78% | 78.38% | 78.38% | 0.6172 | FAIL | FAIL |
| mobilenetv3small | 61.26% | 51.35% | 74.32% | 58.11% | 0.6104 | FAIL | FAIL |
| efficientnetv2b0 | 59.46% | 41.89% | 64.86% | 71.62% | 0.5875 | FAIL | FAIL |

## Decision

- Mejor modelo medido: `baseline_modelo_vivero_tflite`.
- Mejor modelo entrenado en fase 4: `mobilenetv2`.
- Aprobado para diagnostico final: `no`.
- Aprobado para reemplazar backend: `no`.
- Uso recomendado: `filtro_rapido_por_grupo_no_diagnostico_final`.
- Razon: Ningun modelo alcanza accuracy>=80%, atencion>=70% y peligro>=80%.

## Implicacion

El modelo local puede seguir siendo util como filtro rapido y para agregacion por grupo, pero no debe presentarse como diagnostico final autonomo. La siguiente fase debe aplicar reglas de confianza y escalamiento a captura adicional, revision manual o Gemini.
