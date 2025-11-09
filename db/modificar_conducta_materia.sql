-- ============================================================
-- Script para modificar tabla conducta_materia_periodo
-- Agregar columna para conducta literal (MB, B, R, D)
-- ============================================================

-- Paso 1: Agregar columna para conducta literal
ALTER TABLE conducta_materia_periodo
ADD COLUMN conducta_literal VARCHAR(2) NULL 
COMMENT 'Conducta en formato literal: E (Excelente 10-9), MB (Muy Bueno 8-7), B (Bueno 6-5), R (Regular 4-3), NM (Necesita Mejorar 2-1)'
AFTER nota_conducta;

-- Paso 2: Modificar la columna nota_conducta para que sea nullable
-- (puede tener nota O letra, no necesariamente ambas)
ALTER TABLE conducta_materia_periodo
MODIFY COLUMN nota_conducta DECIMAL(4,2) NULL;

-- Paso 3: Agregar llave única para evitar duplicados
ALTER TABLE conducta_materia_periodo
ADD CONSTRAINT uk_conducta_estudiante_asignacion_periodo 
UNIQUE KEY (id_estudiante, id_asignacion, id_periodo);

-- Paso 4: Verificar la estructura
DESCRIBE conducta_materia_periodo;

-- ============================================================
-- Resultado esperado:
-- - nota_conducta: DECIMAL(4,2) NULL (numérica 0-10)
-- - conducta_literal: VARCHAR(2) NULL (MB, B, R, D)
-- - Llave única para evitar duplicados
-- ============================================================
