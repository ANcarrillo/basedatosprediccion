-- Roles base y un usuario de PRUEBA por rol
-- Contraseña de todos los usuarios de prueba: Desercion2026  (cámbiela en la pantalla Usuarios)
-- Ejecutar: psql -U postgres -d desercion_db -f roles_y_usuarios.sql
BEGIN;
INSERT INTO roles (nombre, descripcion) VALUES
    ('administrador', 'Gestiona usuarios, catálogos y el modelo de ML'),
    ('coordinador',   'Coordinador de programa: consulta estudiantes, reportes y gestiona alertas'),
    ('docente',       'Docente / consejero: consulta estudiantes asignados y registra intervenciones'),
    ('bienestar',     'Bienestar Universitario: atiende alertas y registra intervenciones')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO usuarios (nombres, apellidos, email, password_hash, rol_id)
SELECT v.nombres, v.apellidos, v.email, v.hash, r.id FROM (VALUES
    ('Ana', 'Administradora', 'admin@universidad.edu.co', '$2b$12$ROO/dI1VXHuFeTWFk7XI/uMcvEtu2TCU8dNO6DfzbES3odqhUnruG', 'administrador'),
    ('Carlos', 'Coordinador', 'coordinador@universidad.edu.co', '$2b$12$GHiVWqq086cS2SAndO4YX.BJ8ch7c2y9.dxVo5HzyL.N1JdQUWCW6', 'coordinador'),
    ('Diana', 'Docente', 'docente@universidad.edu.co', '$2b$12$IuIPQHgf/PctyW3NshWMcuRd5FezY.nf4bHQoJQnq5dln29qwp3o.', 'docente'),
    ('Beatriz', 'Bienestar', 'bienestar@universidad.edu.co', '$2b$12$7fF8h5cZLTTvVFklzW6vvuGZCdPabU5VIfj0iQJENcyRP5uMAxUjW', 'bienestar')
) AS v(nombres, apellidos, email, hash, rol)
JOIN roles r ON r.nombre = v.rol
ON CONFLICT (email) DO NOTHING;
COMMIT;
