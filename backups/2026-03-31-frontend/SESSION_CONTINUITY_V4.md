# Session Continuity V4 - Frontend Focus

## Propósito
Este documento establece el punto de partida oficial para el desarrollo del **Frontend Web Local** del proyecto Vivero-IA. A partir de esta versión, se establece una división clara de responsabilidades de respaldo.

---

## 1. Reglas de Trabajo y Backup (Persistentes)

Para asegurar que ninguna sesión pierda progreso, se han definido dos comandos de respaldo obligatorios al finalizar cada sesión:

### A. Comando: "guarda todo codex" (RESPALDO BACKEND)
- **Acción**: Crea un snapshot completo en la rama `backup`.
- **Carpeta**: `backups/YYYY-MM-DD-backend/`
- **Contenido**: Código Java, scripts de IA y configuración de infraestructura.

### B. Comando: "guarda todo gemini" (RESPALDO FRONTEND)
- **Acción**: Crea un snapshot completo en la rama `backup-frontend`.
- **Carpeta**: `backups/YYYY-MM-DD-frontend/`
- **Contenido**: Aplicación React, componentes UI, hooks y lógica de integración.

**NOTA**: Cada vez que se inicie un nuevo chat, se DEBE leer este documento para entender la jerarquía de ramas y carpetas de respaldo.

---

## 2. Estado Actual del Frontend
- **Tecnología**: React + Vite + Tailwind + shadcn/ui.
- **Estado**: Pendiente de inicialización en la carpeta `vivero-frontend/`.
- **Próxima Acción**: Crear la estructura base del frontend y conectar con el Auth del backend.

---

## 3. Plan de Trabajo Inmediato (Próxima Sesión)
1. Crear carpeta `vivero-frontend/`.
2. Ejecutar `npm create vite@latest . -- --template react-ts`.
3. Configurar Tailwind CSS y shadcn/ui.
4. Implementar el módulo de autenticación (Login + Persistencia de Token).

---

## 4. Instrucción para Gemini (Próxima Sesión)
Al iniciar, leer `documentacion_local_raiz/SESSION_CONTINUITY_V4.md`.
Verificar que el backend esté corriendo en el puerto 8080.
Cambiar a la rama `funcionalidad/interfaz-web` (o crearla si no existe).
