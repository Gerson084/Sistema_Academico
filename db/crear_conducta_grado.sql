-- Crear tabla para conducta final anual por grado
CREATE TABLE IF NOT EXISTS conducta_grado_periodo (
    id_conducta_grado INT AUTO_INCREMENT PRIMARY KEY,
    id_estudiante INT NOT NULL,
    id_seccion INT NOT NULL,
    id_ano_lectivo INT NOT NULL,
    nota_conducta_final DECIMAL(4,2) NULL,
    conducta_literal VARCHAR(2) NULL CHECK (conducta_literal IN ('E', 'MB', 'B', 'R', 'NM')),
    observacion_general TEXT NULL,
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante) ON DELETE CASCADE,
    FOREIGN KEY (id_seccion) REFERENCES secciones(id_seccion) ON DELETE CASCADE,
    FOREIGN KEY (id_ano_lectivo) REFERENCES anos_lectivos(id_ano_lectivo) ON DELETE CASCADE,
    UNIQUE KEY uk_conducta_grado_unica (id_estudiante, id_seccion, id_ano_lectivo),
    CHECK ((nota_conducta_final IS NOT NULL AND conducta_literal IS NULL) OR 
           (nota_conducta_final IS NULL AND conducta_literal IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices para mejorar el rendimiento
CREATE INDEX idx_conducta_seccion_ano ON conducta_grado_periodo(id_seccion, id_ano_lectivo);
CREATE INDEX idx_conducta_estudiante ON conducta_grado_periodo(id_estudiante);
