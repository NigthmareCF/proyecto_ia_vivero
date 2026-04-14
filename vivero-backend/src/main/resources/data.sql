-- ══════════════════════════════════════════════════════
-- data.sql — seed data inicial del sistema
-- Se ejecuta una sola vez al crear la base de datos
-- ══════════════════════════════════════════════════════

-- Usuario administrador por defecto
-- Password: Admin2026! (encriptado con BCrypt factor 12)
-- CAMBIAR en producción antes de desplegar
INSERT INTO users (
    first_name, last_name, email, password, role, active,
    auth_provider, email_verified, last_login_at, created_at, updated_at
)
VALUES (
    'System',
    'Admin',
    'admin@vivero.com',
    '$2a$12$XVUlSMGpjrCQaVISvfAWyuRd9nKZ8CwFtB3XeAV9eV6m1JOyDRn2K',
    'ADMIN',
    true,
    'LOCAL',
    true,
    NOW(),
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Configuración base de notificación para pruebas manuales del módulo reports
INSERT INTO notification_config (user_id, channel, contact_value, active, created_at, updated_at)
SELECT
    u.id,
    'EMAIL',
    'admin@vivero.com',
    true,
    NOW(),
    NOW()
FROM users u
WHERE u.email = 'admin@vivero.com'
  AND NOT EXISTS (
      SELECT 1
      FROM notification_config nc
      WHERE nc.user_id = u.id
        AND nc.channel = 'EMAIL'
  );

-- Reporte semilla para validar listado y descarga PDF despues de crear la base
INSERT INTO reports (
    patrol_id,
    generated_by,
    title,
    summary,
    observations_count,
    healthy_count,
    attention_count,
    danger_count,
    pdf_path,
    created_at,
    updated_at
)
SELECT
    1001,
    u.id,
    'Seed Report - Initial Patrol Validation',
    'Reporte semilla para validar el flujo manual del modulo reports.',
    3,
    1,
    1,
    1,
    NULL,
    NOW(),
    NOW()
FROM users u
WHERE u.email = 'admin@vivero.com'
  AND NOT EXISTS (
      SELECT 1
      FROM reports r
      WHERE r.patrol_id = 1001
        AND r.title = 'Seed Report - Initial Patrol Validation'
  );
