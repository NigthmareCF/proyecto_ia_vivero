# Backup estado pre-Nginx - 2026-05-27

Rama: `principal`
Worktree: `C:\Proyecto_IA_Vivero\worktrees\release`
Objetivo: dejar un punto de respaldo remoto antes de convertir el frontend/back a entrada unica por Nginx.

## Incluido en el respaldo Git

- Cambios actuales de frontend y backend en `worktrees/release`.
- Documentacion operativa existente.
- Archivos de despliegue VM/Nginx no secretos si estan presentes.
- Guardas de render/polyfill frontend si estan presentes.

## Excluido del respaldo Git

- `.env`: contiene credenciales/API keys reales y queda solo local.
- `robot-pi/.env`: contiene configuracion local del runtime fisico y queda solo local.
- `backups/*.sql`, `backups/*.tar.gz`, `backups/*.zip`: artefactos pesados/locales, no aptos para commit ordinario.
- Logs temporales y cache local.

## Nota operativa

El cambio posterior de Nginx debe limitarse al frontend, backend y compose del stack web. No debe modificar la logica del runtime del robot.
