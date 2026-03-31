package com.vivero.shared.enums;

/**
 * Modos de operación del robot.
 *
 * AUTO   → seguimiento de línea autónomo, el robot decide su movimiento
 * MANUAL → control por teclado/mouse desde la interfaz, línea deshabilitada
 * IDLE   → detenido, en espera de instrucciones
 * GOTO   → navegación autónoma hacia una planta específica por QR
 */
public enum RobotMode {
    AUTO,
    MANUAL,
    IDLE,
    GOTO
}
