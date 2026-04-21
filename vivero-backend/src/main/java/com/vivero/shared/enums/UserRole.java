package com.vivero.shared.enums;

/**
 * Roles disponibles en el sistema.
 * Determina qué puede hacer cada usuario en la interfaz y la API.
 *
 * ADMIN      → acceso total: gestión de usuarios, control del robot, reportes
 * CONTROLLER → control del robot, reportes y operación general
 * VIEWER     → solo lectura: ver reportes y estado de plantas
 */
public enum UserRole {
    ADMIN,
    CONTROLLER,
    VIEWER
}
