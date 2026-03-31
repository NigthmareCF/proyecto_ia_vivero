package com.vivero.shared.enums;

/**
 * Estados posibles de salud de una planta.
 * Definidos por el modelo de IA y también asignables manualmente por el operador.
 *
 * HEALTHY   → planta en buen estado, sin signos de problema
 * ATTENTION → signos tempranos de estrés o deficiencia, requiere monitoreo
 * DANGER    → estado crítico, intervención inmediata requerida
 * UNKNOWN   → sin clasificación aún (planta recién registrada o sin patrullaje)
 */
public enum PlantState {
    HEALTHY,
    ATTENTION,
    DANGER,
    UNKNOWN
}
