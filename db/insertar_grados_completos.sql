-- Insertar todos los grados del sistema educativo salvadoreño
-- IMPORTANTE: Ejecuta primero agregar_orden_grados.sql para crear el campo orden

-- Eliminar grados existentes si quieres empezar de cero (OPCIONAL - CUIDADO)
-- DELETE FROM grados;

-- PARVULARIA (Orden 1-4)
INSERT INTO grados (nombre_grado, nivel, orden, activo) VALUES
('Inicial', 'Parvularia', 1, 1),
('PreKinder', 'Parvularia', 2, 1),
('Kinder', 'Parvularia', 3, 1),
('Preparatoria', 'Parvularia', 4, 1),
('Primer Grado', 'Básico', 5, 1);

-- BÁSICO (Orden 5-13)
INSERT INTO grados (nombre_grado, nivel, orden, activo) VALUES
('Segundo Grado', 'Básico', 6, 1),
('Tercer Grado', 'Básico', 7, 1),
('Cuarto Grado', 'Básico', 8, 1),
('Quinto Grado', 'Básico', 9, 1),
('Sexto Grado', 'Básico', 10, 1),
('Séptimo Grado', 'Básico', 11, 1),
('Octavo Grado', 'Básico', 12, 1),
('Noveno Grado', 'Básico', 13, 1);

-- BACHILLERATO (Orden 14-16)
INSERT INTO grados (nombre_grado, nivel, orden, activo) VALUES
('Primer Año Bachillerato', 'Bachillerato', 14, 1),
('Segundo Año Bachillerato', 'Bachillerato', 15, 1),

-- Verificar que todos los grados se insertaron correctamente
SELECT id_grado, nombre_grado, nivel, orden, activo FROM grados ORDER BY orden;
