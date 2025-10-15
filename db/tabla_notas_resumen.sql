-- ======================================
-- TABLA PARA GUARDAR RESUMEN DE NOTAS POR PERÍODO
-- ======================================

-- Esta tabla almacena el resumen calculado de todas las notas de un estudiante
-- en una asignación específica durante un período

CREATE TABLE IF NOT EXISTS notas_resumen_periodo (
    id_resumen INT PRIMARY KEY AUTO_INCREMENT,
    id_estudiante INT NOT NULL,
    id_asignacion INT NOT NULL,
    id_periodo INT NOT NULL,
    
    -- Promedio de actividades (30%)
    promedio_actividades DECIMAL(4,2) NULL,
    porcentaje_actividades DECIMAL(4,2) NULL COMMENT 'promedio_actividades * 0.30',
    
    -- Nota Revisión de Cuaderno (5%)
    nota_rc DECIMAL(4,2) NULL,
    porcentaje_rc DECIMAL(4,2) NULL COMMENT 'nota_rc * 0.05',
    
    -- Integradoras individuales
    integradora_1 DECIMAL(4,2) NULL COMMENT '25%',
    integradora_2 DECIMAL(4,2) NULL COMMENT '5%',
    integradora_3 DECIMAL(4,2) NULL COMMENT '5%',
    
    -- Total integradoras (35%)
    promedio_integradoras DECIMAL(4,2) NULL,
    porcentaje_integradoras DECIMAL(4,2) NULL COMMENT 'suma ponderada de integradoras',
    
    -- Total Base Integradora (70%)
    total_bi DECIMAL(4,2) NULL COMMENT 'act(30%) + rc(5%) + int(35%)',
    
    -- Prueba Objetiva (30%)
    prueba_objetiva DECIMAL(4,2) NULL,
    porcentaje_po DECIMAL(4,2) NULL COMMENT 'prueba_objetiva * 0.30',
    
    -- Nota Final del Período (100%)
    nota_final_periodo DECIMAL(4,2) NULL COMMENT 'total_bi + porcentaje_po',
    
    -- Actitud
    nota_actitud VARCHAR(50) NULL,
    
    -- Control
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Llaves foráneas
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante) ON DELETE CASCADE,
    FOREIGN KEY (id_asignacion) REFERENCES materia_seccion(id_asignacion) ON DELETE CASCADE,
    FOREIGN KEY (id_periodo) REFERENCES periodos(id_periodo) ON DELETE CASCADE,
    
    -- Un estudiante solo puede tener un resumen por asignación y período
    UNIQUE KEY uk_estudiante_asignacion_periodo (id_estudiante, id_asignacion, id_periodo),
    
    -- Índices para consultas rápidas
    INDEX idx_estudiante (id_estudiante),
    INDEX idx_asignacion (id_asignacion),
    INDEX idx_periodo (id_periodo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Almacena el resumen calculado de notas por estudiante, asignación y período';

-- Vista para consultar fácilmente las notas con información completa
CREATE OR REPLACE VIEW vista_notas_completas AS
SELECT 
    nr.id_resumen,
    e.id_estudiante,
    e.nie,
    CONCAT(e.apellidos, ', ', e.nombres) as nombre_completo,
    m.id_materia,
    m.nombre_materia,
    m.codigo_materia,
    s.id_seccion,
    s.nombre_seccion,
    g.nombre_grado,
    g.nivel,
    p.id_periodo,
    p.nombre_periodo,
    p.numero_periodo,
    al.ano as ano_lectivo,
    
    -- Notas
    nr.promedio_actividades,
    nr.porcentaje_actividades,
    nr.nota_rc,
    nr.porcentaje_rc,
    nr.integradora_1,
    nr.integradora_2,
    nr.integradora_3,
    nr.promedio_integradoras,
    nr.porcentaje_integradoras,
    nr.total_bi,
    nr.prueba_objetiva,
    nr.porcentaje_po,
    nr.nota_final_periodo,
    nr.nota_actitud,
    
    -- Estado
    CASE 
        WHEN nr.nota_final_periodo >= 7.0 THEN 'Aprobado'
        WHEN nr.nota_final_periodo >= 5.0 THEN 'En Recuperación'
        WHEN nr.nota_final_periodo > 0 THEN 'Reprobado'
        ELSE 'Sin Calificar'
    END as estado_nota,
    
    nr.fecha_ingreso,
    nr.fecha_actualizacion
    
FROM notas_resumen_periodo nr
INNER JOIN estudiantes e ON nr.id_estudiante = e.id_estudiante
INNER JOIN materia_seccion ms ON nr.id_asignacion = ms.id_asignacion
INNER JOIN materias m ON ms.id_materia = m.id_materia
INNER JOIN secciones s ON ms.id_seccion = s.id_seccion
INNER JOIN grados g ON s.id_grado = g.id_grado
INNER JOIN periodos p ON nr.id_periodo = p.id_periodo
INNER JOIN anos_lectivos al ON p.id_ano_lectivo = al.id_ano_lectivo;
