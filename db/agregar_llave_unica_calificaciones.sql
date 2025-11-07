-- Script para agregar llave única a la tabla calificaciones
-- Esto previene que se guarden notas duplicadas

-- Paso 1: Verificar si ya existe la llave única
SELECT 
    COUNT(*) as existe_llave
FROM information_schema.TABLE_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = DATABASE()
  AND TABLE_NAME = 'calificaciones'
  AND CONSTRAINT_NAME = 'uk_calificacion_unica';

-- Paso 2: Agregar la llave única (ejecutar solo si el paso 1 devuelve 0)
ALTER TABLE calificaciones
ADD CONSTRAINT uk_calificacion_unica 
UNIQUE KEY (id_estudiante, id_asignacion, id_periodo, id_tipo_evaluacion);

-- Paso 3: Verificar que se creó correctamente
SHOW INDEX FROM calificaciones WHERE Key_name = 'uk_calificacion_unica';

-- Resultado esperado: 4 filas (una por cada columna en la llave compuesta)
