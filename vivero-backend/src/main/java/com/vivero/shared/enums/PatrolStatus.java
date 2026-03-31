package com.vivero.shared.enums;

/**
 * Estados del ciclo de vida de un patrullaje.
 *
 * PENDING     → creado pero el robot aún no inició el recorrido
 * IN_PROGRESS → robot en movimiento, clasificando plantas
 * COMPLETED   → recorrido finalizado correctamente
 * ABORTED     → interrumpido manualmente o por error del robot
 */
public enum PatrolStatus {
    PENDING,
    IN_PROGRESS,
    COMPLETED,
    ABORTED
}
