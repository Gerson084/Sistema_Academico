-- Agregar campo orden a la tabla grados
ALTER TABLE grados ADD COLUMN orden INT NOT NULL DEFAULT 0 AFTER nivel;

-- Actualizar el orden de los grados existentes
-- Parvularia (1-4)
UPDATE grados SET orden = 1 WHERE nombre_grado = 'Inicial' AND nivel = 'Parvularia';
UPDATE grados SET orden = 2 WHERE nombre_grado LIKE '%PreKinder%' AND nivel = 'Parvularia';
UPDATE grados SET orden = 3 WHERE nombre_grado LIKE '%Kinder%' AND nivel = 'Parvularia' AND nombre_grado NOT LIKE '%Pre%';
UPDATE grados SET orden = 4 WHERE nombre_grado = 'Preparatoria' AND nivel = 'Parvularia';
UPDATE grados SET orden = 5 WHERE nombre_grado LIKE '%Primer%' AND nivel = 'Parvularia';


-- Básico (5-13)
UPDATE grados SET orden = 6 WHERE nombre_grado LIKE '%Segundo%' AND nivel = 'Básico';
UPDATE grados SET orden = 7 WHERE nombre_grado LIKE '%Tercer%' AND nivel = 'Básico';
UPDATE grados SET orden = 8 WHERE nombre_grado LIKE '%Cuarto%' AND nivel = 'Básico';
UPDATE grados SET orden = 9 WHERE nombre_grado LIKE '%Quinto%' AND nivel = 'Básico';
UPDATE grados SET orden = 10 WHERE nombre_grado LIKE '%Sexto%' AND nivel = 'Básico';
UPDATE grados SET orden = 11 WHERE nombre_grado LIKE '%S%ptimo%' AND nivel = 'Básico';
UPDATE grados SET orden = 12 WHERE nombre_grado LIKE '%Octavo%' AND nivel = 'Básico';
UPDATE grados SET orden = 13 WHERE nombre_grado LIKE '%Noveno%' AND nivel = 'Básico';

-- Bachillerato (14-16)
UPDATE grados SET orden = 14 WHERE nombre_grado LIKE '%Primer%' AND nivel = 'Bachillerato';
UPDATE grados SET orden = 15 WHERE nombre_grado LIKE '%Segundo%' AND nivel = 'Bachillerato';

-- Verificar los cambios
SELECT id_grado, nombre_grado, nivel, orden, activo FROM grados ORDER BY orden;
