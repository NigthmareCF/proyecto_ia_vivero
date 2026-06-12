-- ══════════════════════════════════════════════════════
-- data.sql — seed data inicial del sistema
-- Se ejecuta una sola vez al crear la base de datos
-- ══════════════════════════════════════════════════════

-- Usuario administrador por defecto
-- Password: Admin2026! (encriptado con BCrypt factor 12)
-- CAMBIAR en producción antes de desplegar
INSERT INTO users (first_name, last_name, email, password, role, active, created_at, updated_at)
SELECT
    'System',
    'Admin',
    'admin@vivero.com',
    '$2a$12$XVUlSMGpjrCQaVISvfAWyuRd9nKZ8CwFtB3XeAV9eV6m1JOyDRn2K',
    'ADMIN',
    true,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM users
    WHERE email = 'admin@vivero.com'
);

-- Usuario adminMov para pruebas de acceso desde dispositivos moviles
-- Password: AdminMov2026! (encriptado con BCrypt factor 12)
INSERT INTO users (first_name, last_name, email, password, role, active, created_at, updated_at)
SELECT
    'Mobile',
    'Admin',
    'adminMov@vivero.com',
    '$2a$12$D1X/i7fdMy33URjBbS1k6.8mN9S.YGAgsNNeqeN5KKtb3RGcb9REG',
    'ADMIN',
    true,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1
    FROM users
    WHERE email = 'adminMov@vivero.com'
);

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
    manual_review_count,
    inconclusive_count,
    plant_details_json,
    pdf_path,
    public_share_token,
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
    0,
    0,
    NULL,
    NULL,
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
