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
