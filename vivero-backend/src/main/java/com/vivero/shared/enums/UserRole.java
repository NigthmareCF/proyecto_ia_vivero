package com.vivero.shared.enums;

/**
 * Roles disponibles en el sistema.
 * Determina qué puede hacer cada usuario en la interfaz y la API.
 *
 * ADMIN    → acceso total: gestión de usuarios, control del robot, reportes
 * OPERATOR → control del robot, ver y crear observaciones manuales, ver reportes
 * VIEWER   → solo lectura: ver reportes y estado de plantas
 */
public enum UserRole {
    ADMIN,
    OPERATOR,
    VIEWER
}
