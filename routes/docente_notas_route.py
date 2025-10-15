from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.MateriaSeccion import MateriaSeccion
from models.Materias import Materia
from models.Secciones import Seccion
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo
from models.Periodos import Periodo
from models.Estudiantes import Estudiante
from models.matriculas import Matricula
from models.usuarios import Usuario
from db import db
from sqlalchemy import text
from datetime import datetime

docente_notas_bp = Blueprint('docente_notas', __name__, template_folder='templates')

@docente_notas_bp.route('/mis-materias')
def mis_materias():
    """Muestra las materias asignadas al docente en formato cards con filtros"""
    # Obtener el ID del docente desde la sesión
    id_docente = session.get('user_id')
    print(f"DEBUG - Session: {dict(session)}")
    print(f"DEBUG - ID Docente: {id_docente}")
    
    if not id_docente:
        print("DEBUG - No hay id_docente, redirigiendo al login")
        return redirect(url_for('auth.login'))
    
    # Filtros opcionales
    ano_seleccionado = request.args.get('ano_lectivo', type=int)
    
    try:
        # Query para obtener las asignaciones del docente
        query = text("""
            SELECT 
                ms.id_asignacion,
                m.id_materia,
                m.nombre_materia,
                m.codigo_materia,
                s.id_seccion,
                s.nombre_seccion,
                g.id_grado,
                g.nombre_grado,
                g.nivel,
                al.id_ano_lectivo,
                al.ano as ano_lectivo,
                al.activo as ano_activo,
                (SELECT COUNT(*) FROM matriculas mat 
                 WHERE mat.id_seccion = s.id_seccion AND mat.activa = 1) as total_estudiantes
            FROM materia_seccion ms
            INNER JOIN materias m ON ms.id_materia = m.id_materia
            INNER JOIN secciones s ON ms.id_seccion = s.id_seccion
            INNER JOIN grados g ON s.id_grado = g.id_grado
            INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
            WHERE ms.id_maestro = :id_docente
            AND m.activa = 1
            AND s.activo = 1
            AND (:ano_lectivo IS NULL OR al.id_ano_lectivo = :ano_lectivo)
            ORDER BY al.ano DESC, g.nombre_grado, s.nombre_seccion, m.nombre_materia
        """)
        
        result = db.session.execute(query, {
            'id_docente': id_docente,
            'ano_lectivo': ano_seleccionado
        })
        
        asignaciones = []
        for row in result:
            asignaciones.append({
                'id_asignacion': row.id_asignacion,
                'id_materia': row.id_materia,
                'nombre_materia': row.nombre_materia,
                'codigo_materia': row.codigo_materia,
                'id_seccion': row.id_seccion,
                'nombre_seccion': row.nombre_seccion,
                'id_grado': row.id_grado,
                'nombre_grado': row.nombre_grado,
                'nivel': row.nivel,
                'id_ano_lectivo': row.id_ano_lectivo,
                'ano_lectivo': row.ano_lectivo,
                'ano_activo': row.ano_activo,
                'total_estudiantes': row.total_estudiantes
            })
        
        # Obtener años lectivos para el filtro
        anos_lectivos = AnoLectivo.query.order_by(AnoLectivo.ano.desc()).all()
        
        return render_template('notas/mis_materias.html',
                             asignaciones=asignaciones,
                             anos_lectivos=anos_lectivos,
                             ano_seleccionado=ano_seleccionado)
        
    except Exception as e:
        print(f"Error al obtener materias: {str(e)}")
        return render_template('notas/mis_materias.html',
                             asignaciones=[],
                             anos_lectivos=[],
                             error="Error al cargar las materias")


@docente_notas_bp.route('/ingresar-notas/<int:id_asignacion>')
def ingresar_notas(id_asignacion):
    """Muestra el formulario para ingresar notas de una asignación específica"""
    id_docente = session.get('user_id')
    
    if not id_docente:
        return redirect(url_for('auth.login'))
    
    # Verificar que la asignación pertenece al docente
    asignacion = MateriaSeccion.query.filter_by(
        id_asignacion=id_asignacion,
        id_maestro=id_docente
    ).first_or_404()
    
    # Obtener información de la asignación
    query_info = text("""
        SELECT 
            m.nombre_materia,
            m.codigo_materia,
            g.nombre_grado,
            g.nivel,
            s.nombre_seccion,
            al.ano as ano_lectivo,
            al.id_ano_lectivo
        FROM materia_seccion ms
        INNER JOIN materias m ON ms.id_materia = m.id_materia
        INNER JOIN secciones s ON ms.id_seccion = s.id_seccion
        INNER JOIN grados g ON s.id_grado = g.id_grado
        INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
        WHERE ms.id_asignacion = :id_asignacion
    """)
    
    info_result = db.session.execute(query_info, {'id_asignacion': id_asignacion}).first()
    
    # Obtener períodos del año lectivo
    periodos = Periodo.query.filter_by(
        id_ano_lectivo=info_result.id_ano_lectivo
    ).order_by(Periodo.numero_periodo).all()
    
    # Período seleccionado (por defecto el activo o el primero)
    id_periodo = request.args.get('periodo', type=int)
    if not id_periodo:
        periodo_activo = Periodo.query.filter_by(
            id_ano_lectivo=info_result.id_ano_lectivo,
            activo=True
        ).first()
        id_periodo = periodo_activo.id_periodo if periodo_activo else (periodos[0].id_periodo if periodos else None)
    
    # Obtener estudiantes matriculados en la sección
    query_estudiantes = text("""
        SELECT 
            e.id_estudiante,
            e.nie,
            e.nombres,
            e.apellidos,
            mat.id_matricula
        FROM estudiantes e
        INNER JOIN matriculas mat ON e.id_estudiante = mat.id_estudiante
        WHERE mat.id_seccion = :id_seccion
        AND mat.activa = 1
        AND e.activo = 1
        ORDER BY e.apellidos, e.nombres
    """)
    
    estudiantes_result = db.session.execute(query_estudiantes, {'id_seccion': asignacion.id_seccion})
    
    estudiantes = []
    for row in estudiantes_result:
        id_est = row.id_estudiante
        
        # Intentar cargar notas existentes del resumen
        query_notas_existentes = text("""
            SELECT 
                promedio_actividades,
                nota_rc,
                integradora_1,
                integradora_2,
                integradora_3,
                prueba_objetiva,
                nota_actitud
            FROM notas_resumen_periodo
            WHERE id_estudiante = :id_estudiante
            AND id_asignacion = :id_asignacion
            AND id_periodo = :id_periodo
        """)
        
        notas_existentes = db.session.execute(query_notas_existentes, {
            'id_estudiante': id_est,
            'id_asignacion': id_asignacion,
            'id_periodo': id_periodo
        }).first()
        
        # Si existen notas, cargar actividades individuales
        actividades_existentes = {}
        if notas_existentes or True:  # Siempre intentar cargar actividades
            query_actividades = text("""
                SELECT te.nombre_tipo, c.nota
                FROM calificaciones c
                INNER JOIN tipos_evaluacion te ON c.id_tipo_evaluacion = te.id_tipo_evaluacion
                WHERE c.id_estudiante = :id_estudiante
                AND c.id_asignacion = :id_asignacion
                AND c.id_periodo = :id_periodo
                AND te.id_categoria_evaluacion = 1
                AND te.nombre_tipo LIKE 'Actividad%'
                ORDER BY te.nombre_tipo
            """)
            
            actividades_result = db.session.execute(query_actividades, {
                'id_estudiante': id_est,
                'id_asignacion': id_asignacion,
                'id_periodo': id_periodo
            })
            
            for act_row in actividades_result:
                # Extraer número de actividad (ej: "Actividad 1" -> 1)
                numero = act_row.nombre_tipo.replace('Actividad ', '')
                actividades_existentes[f'act{numero}'] = float(act_row.nota) if act_row.nota else None
        
        estudiantes.append({
            'id_estudiante': id_est,
            'nie': row.nie,
            'nombre_completo': f"{row.apellidos}, {row.nombres}",
            'id_matricula': row.id_matricula,
            'notas_existentes': {
                'actividades': actividades_existentes,
                'nota_rc': float(notas_existentes.nota_rc) if notas_existentes and notas_existentes.nota_rc else None,
                'integradora_1': float(notas_existentes.integradora_1) if notas_existentes and notas_existentes.integradora_1 else None,
                'integradora_2': float(notas_existentes.integradora_2) if notas_existentes and notas_existentes.integradora_2 else None,
                'integradora_3': float(notas_existentes.integradora_3) if notas_existentes and notas_existentes.integradora_3 else None,
                'prueba_objetiva': float(notas_existentes.prueba_objetiva) if notas_existentes and notas_existentes.prueba_objetiva else None,
                'actitud': notas_existentes.nota_actitud if notas_existentes and notas_existentes.nota_actitud else ''
            } if notas_existentes else None
        })
    
    info_asignacion = {
        'nombre_materia': info_result.nombre_materia,
        'codigo_materia': info_result.codigo_materia,
        'grado': f"{info_result.nombre_grado} - {info_result.nivel}",
        'seccion': info_result.nombre_seccion,
        'ano_lectivo': info_result.ano_lectivo
    }
    
    return render_template('notas/formato_notas.html',
                         id_asignacion=id_asignacion,
                         info_asignacion=info_asignacion,
                         estudiantes=estudiantes,
                         periodos=periodos,
                         id_periodo=id_periodo)


@docente_notas_bp.route('/guardar-notas/<int:id_asignacion>', methods=['POST'])
def guardar_notas(id_asignacion):
    """Guarda las notas ingresadas por el docente"""
    id_docente = session.get('user_id')
    
    if not id_docente:
        return jsonify({"success": False, "mensaje": "Sesión expirada"})
    
    # Verificar permisos
    asignacion = MateriaSeccion.query.filter_by(
        id_asignacion=id_asignacion,
        id_maestro=id_docente
    ).first()
    
    if not asignacion:
        return jsonify({"success": False, "mensaje": "No tiene permisos para esta asignación"})
    
    try:
        data = request.get_json()
        id_periodo = data.get('id_periodo')
        notas_estudiantes = data.get('notas', [])
        
        if not id_periodo:
            return jsonify({"success": False, "mensaje": "Debe seleccionar un período"})
        
        print(f"DEBUG - Guardando notas para asignación {id_asignacion}, período {id_periodo}")
        print(f"DEBUG - Total estudiantes: {len(notas_estudiantes)}")
        
        # Procesar cada estudiante
        for nota_data in notas_estudiantes:
            id_estudiante = nota_data.get('id_estudiante')
            
            print(f"DEBUG - Procesando estudiante {id_estudiante}")
            
            # 1. GUARDAR ACTIVIDADES (Categoría 1: Actividades - 30%)
            actividades = nota_data.get('actividades', [])
            for actividad in actividades:
                # Buscar o crear el tipo de evaluación para esta actividad
                query_tipo = text("""
                    SELECT id_tipo_evaluacion 
                    FROM tipos_evaluacion 
                    WHERE id_categoria_evaluacion = 1 
                    AND id_asignacion = :id_asignacion
                    AND nombre_tipo = :nombre_tipo
                """)
                
                nombre_actividad = f"Actividad {actividad['numero']}"
                tipo_result = db.session.execute(query_tipo, {
                    'id_asignacion': id_asignacion,
                    'nombre_tipo': nombre_actividad
                }).first()
                
                if not tipo_result:
                    # Crear el tipo de evaluación
                    insert_tipo = text("""
                        INSERT INTO tipos_evaluacion 
                        (id_categoria_evaluacion, id_asignacion, nombre_tipo, porcentaje)
                        VALUES (1, :id_asignacion, :nombre_tipo, NULL)
                    """)
                    db.session.execute(insert_tipo, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_actividad
                    })
                    db.session.flush()
                    
                    # Obtener el ID recién creado
                    tipo_result = db.session.execute(query_tipo, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_actividad
                    }).first()
                
                id_tipo_evaluacion = tipo_result[0]
                
                # Insertar o actualizar la calificación
                upsert_calificacion = text("""
                    INSERT INTO calificaciones 
                    (id_estudiante, id_asignacion, id_periodo, id_tipo_evaluacion, nota)
                    VALUES (:id_estudiante, :id_asignacion, :id_periodo, :id_tipo_evaluacion, :nota)
                    ON DUPLICATE KEY UPDATE nota = :nota, fecha_ingreso = CURRENT_TIMESTAMP
                """)
                
                db.session.execute(upsert_calificacion, {
                    'id_estudiante': id_estudiante,
                    'id_asignacion': id_asignacion,
                    'id_periodo': id_periodo,
                    'id_tipo_evaluacion': id_tipo_evaluacion,
                    'nota': actividad['nota']
                })
            
            # 2. GUARDAR NOTA R.C (puede ser categoría especial o parte de actividades)
            if nota_data.get('nota_rc') is not None:
                # Guardar R.C como un tipo especial
                nombre_rc = "Revisión de Cuaderno"
                query_tipo_rc = text("""
                    SELECT id_tipo_evaluacion 
                    FROM tipos_evaluacion 
                    WHERE id_categoria_evaluacion = 1 
                    AND id_asignacion = :id_asignacion
                    AND nombre_tipo = :nombre_tipo
                """)
                
                tipo_rc_result = db.session.execute(query_tipo_rc, {
                    'id_asignacion': id_asignacion,
                    'nombre_tipo': nombre_rc
                }).first()
                
                if not tipo_rc_result:
                    insert_tipo_rc = text("""
                        INSERT INTO tipos_evaluacion 
                        (id_categoria_evaluacion, id_asignacion, nombre_tipo, porcentaje)
                        VALUES (1, :id_asignacion, :nombre_tipo, 5.00)
                    """)
                    db.session.execute(insert_tipo_rc, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_rc
                    })
                    db.session.flush()
                    tipo_rc_result = db.session.execute(query_tipo_rc, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_rc
                    }).first()
                
                id_tipo_rc = tipo_rc_result[0]
                
                upsert_rc = text("""
                    INSERT INTO calificaciones 
                    (id_estudiante, id_asignacion, id_periodo, id_tipo_evaluacion, nota)
                    VALUES (:id_estudiante, :id_asignacion, :id_periodo, :id_tipo_evaluacion, :nota)
                    ON DUPLICATE KEY UPDATE nota = :nota, fecha_ingreso = CURRENT_TIMESTAMP
                """)
                
                db.session.execute(upsert_rc, {
                    'id_estudiante': id_estudiante,
                    'id_asignacion': id_asignacion,
                    'id_periodo': id_periodo,
                    'id_tipo_evaluacion': id_tipo_rc,
                    'nota': nota_data['nota_rc']
                })
            
            # 3. GUARDAR INTEGRADORAS (Categoría 2: Exámenes - 60% -> usaremos para integradoras)
            integradoras = nota_data.get('integradoras', [])
            for integradora in integradoras:
                nombre_integradora = f"Integradora {integradora['numero']}"
                
                query_tipo_int = text("""
                    SELECT id_tipo_evaluacion 
                    FROM tipos_evaluacion 
                    WHERE id_categoria_evaluacion = 2 
                    AND id_asignacion = :id_asignacion
                    AND nombre_tipo = :nombre_tipo
                """)
                
                tipo_int_result = db.session.execute(query_tipo_int, {
                    'id_asignacion': id_asignacion,
                    'nombre_tipo': nombre_integradora
                }).first()
                
                if not tipo_int_result:
                    insert_tipo_int = text("""
                        INSERT INTO tipos_evaluacion 
                        (id_categoria_evaluacion, id_asignacion, nombre_tipo, porcentaje)
                        VALUES (2, :id_asignacion, :nombre_tipo, :porcentaje)
                    """)
                    db.session.execute(insert_tipo_int, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_integradora,
                        'porcentaje': integradora['porcentaje']
                    })
                    db.session.flush()
                    tipo_int_result = db.session.execute(query_tipo_int, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_integradora
                    }).first()
                
                id_tipo_int = tipo_int_result[0]
                
                upsert_int = text("""
                    INSERT INTO calificaciones 
                    (id_estudiante, id_asignacion, id_periodo, id_tipo_evaluacion, nota)
                    VALUES (:id_estudiante, :id_asignacion, :id_periodo, :id_tipo_evaluacion, :nota)
                    ON DUPLICATE KEY UPDATE nota = :nota, fecha_ingreso = CURRENT_TIMESTAMP
                """)
                
                db.session.execute(upsert_int, {
                    'id_estudiante': id_estudiante,
                    'id_asignacion': id_asignacion,
                    'id_periodo': id_periodo,
                    'id_tipo_evaluacion': id_tipo_int,
                    'nota': integradora['nota']
                })
            
            # Extraer valores de integradoras para el resumen
            int1_nota = None
            int2_nota = None
            int3_nota = None
            for integradora in integradoras:
                if integradora['numero'] == 1:
                    int1_nota = integradora['nota']
                elif integradora['numero'] == 2:
                    int2_nota = integradora['nota']
                elif integradora['numero'] == 3:
                    int3_nota = integradora['nota']
            
            # 4. GUARDAR PRUEBA OBJETIVA
            if nota_data.get('prueba_objetiva') is not None:
                nombre_po = "Prueba Objetiva"
                
                query_tipo_po = text("""
                    SELECT id_tipo_evaluacion 
                    FROM tipos_evaluacion 
                    WHERE id_categoria_evaluacion = 2 
                    AND id_asignacion = :id_asignacion
                    AND nombre_tipo = :nombre_tipo
                """)
                
                tipo_po_result = db.session.execute(query_tipo_po, {
                    'id_asignacion': id_asignacion,
                    'nombre_tipo': nombre_po
                }).first()
                
                if not tipo_po_result:
                    insert_tipo_po = text("""
                        INSERT INTO tipos_evaluacion 
                        (id_categoria_evaluacion, id_asignacion, nombre_tipo, porcentaje)
                        VALUES (2, :id_asignacion, :nombre_tipo, 30.00)
                    """)
                    db.session.execute(insert_tipo_po, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_po
                    })
                    db.session.flush()
                    tipo_po_result = db.session.execute(query_tipo_po, {
                        'id_asignacion': id_asignacion,
                        'nombre_tipo': nombre_po
                    }).first()
                
                id_tipo_po = tipo_po_result[0]
                
                upsert_po = text("""
                    INSERT INTO calificaciones 
                    (id_estudiante, id_asignacion, id_periodo, id_tipo_evaluacion, nota)
                    VALUES (:id_estudiante, :id_asignacion, :id_periodo, :id_tipo_evaluacion, :nota)
                    ON DUPLICATE KEY UPDATE nota = :nota, fecha_ingreso = CURRENT_TIMESTAMP
                """)
                
                db.session.execute(upsert_po, {
                    'id_estudiante': id_estudiante,
                    'id_asignacion': id_asignacion,
                    'id_periodo': id_periodo,
                    'id_tipo_evaluacion': id_tipo_po,
                    'nota': nota_data['prueba_objetiva']
                })
            
            # 5. GUARDAR RESUMEN EN TABLA notas_resumen_periodo
            # Primero verificar si la tabla existe, si no, crearla
            try:
                check_table = text("""
                    CREATE TABLE IF NOT EXISTS notas_resumen_periodo (
                        id_resumen INT PRIMARY KEY AUTO_INCREMENT,
                        id_estudiante INT NOT NULL,
                        id_asignacion INT NOT NULL,
                        id_periodo INT NOT NULL,
                        promedio_actividades DECIMAL(4,2) NULL,
                        porcentaje_actividades DECIMAL(4,2) NULL,
                        nota_rc DECIMAL(4,2) NULL,
                        porcentaje_rc DECIMAL(4,2) NULL,
                        integradora_1 DECIMAL(4,2) NULL,
                        integradora_2 DECIMAL(4,2) NULL,
                        integradora_3 DECIMAL(4,2) NULL,
                        promedio_integradoras DECIMAL(4,2) NULL,
                        porcentaje_integradoras DECIMAL(4,2) NULL,
                        total_bi DECIMAL(4,2) NULL,
                        prueba_objetiva DECIMAL(4,2) NULL,
                        porcentaje_po DECIMAL(4,2) NULL,
                        nota_final_periodo DECIMAL(4,2) NULL,
                        nota_actitud VARCHAR(50) NULL,
                        fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
                        FOREIGN KEY (id_asignacion) REFERENCES materia_seccion(id_asignacion),
                        FOREIGN KEY (id_periodo) REFERENCES periodos(id_periodo),
                        UNIQUE KEY uk_estudiante_asignacion_periodo (id_estudiante, id_asignacion, id_periodo)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                db.session.execute(check_table)
                db.session.flush()
            except:
                pass  # La tabla ya existe
            
            # Insertar o actualizar el resumen
            upsert_resumen = text("""
                INSERT INTO notas_resumen_periodo (
                    id_estudiante, id_asignacion, id_periodo,
                    promedio_actividades, porcentaje_actividades,
                    nota_rc, porcentaje_rc,
                    integradora_1, integradora_2, integradora_3,
                    promedio_integradoras, porcentaje_integradoras,
                    total_bi, prueba_objetiva, porcentaje_po,
                    nota_final_periodo, nota_actitud
                ) VALUES (
                    :id_estudiante, :id_asignacion, :id_periodo,
                    :promedio_actividades, :porcentaje_actividades,
                    :nota_rc, :porcentaje_rc,
                    :integradora_1, :integradora_2, :integradora_3,
                    :promedio_integradoras, :porcentaje_integradoras,
                    :total_bi, :prueba_objetiva, :porcentaje_po,
                    :nota_final_periodo, :nota_actitud
                )
                ON DUPLICATE KEY UPDATE
                    promedio_actividades = VALUES(promedio_actividades),
                    porcentaje_actividades = VALUES(porcentaje_actividades),
                    nota_rc = VALUES(nota_rc),
                    porcentaje_rc = VALUES(porcentaje_rc),
                    integradora_1 = VALUES(integradora_1),
                    integradora_2 = VALUES(integradora_2),
                    integradora_3 = VALUES(integradora_3),
                    promedio_integradoras = VALUES(promedio_integradoras),
                    porcentaje_integradoras = VALUES(porcentaje_integradoras),
                    total_bi = VALUES(total_bi),
                    prueba_objetiva = VALUES(prueba_objetiva),
                    porcentaje_po = VALUES(porcentaje_po),
                    nota_final_periodo = VALUES(nota_final_periodo),
                    nota_actitud = VALUES(nota_actitud),
                    fecha_actualizacion = CURRENT_TIMESTAMP
            """)
            
            # Calcular promedio integradoras
            prom_int = None
            if int1_nota or int2_nota or int3_nota:
                count_int = sum([1 for x in [int1_nota, int2_nota, int3_nota] if x is not None])
                sum_int = sum([x for x in [int1_nota, int2_nota, int3_nota] if x is not None])
                prom_int = sum_int / count_int if count_int > 0 else None
            
            # Calcular porcentaje R.C
            porc_rc = (nota_data.get('nota_rc') * 0.05) if nota_data.get('nota_rc') else None
            
            # Calcular porcentaje actividades
            porc_act = (nota_data.get('promedio_actividades') * 0.30) if nota_data.get('promedio_actividades') else None
            
            # Calcular porcentaje integradoras (25%, 5%, 5%)
            porc_int = 0
            if int1_nota:
                porc_int += int1_nota * 0.25
            if int2_nota:
                porc_int += int2_nota * 0.05
            if int3_nota:
                porc_int += int3_nota * 0.05
            porc_int = porc_int if (int1_nota or int2_nota or int3_nota) else None
            
            # Calcular porcentaje P.O
            porc_po = (nota_data.get('prueba_objetiva') * 0.30) if nota_data.get('prueba_objetiva') else None
            
            db.session.execute(upsert_resumen, {
                'id_estudiante': id_estudiante,
                'id_asignacion': id_asignacion,
                'id_periodo': id_periodo,
                'promedio_actividades': nota_data.get('promedio_actividades'),
                'porcentaje_actividades': porc_act,
                'nota_rc': nota_data.get('nota_rc'),
                'porcentaje_rc': porc_rc,
                'integradora_1': int1_nota,
                'integradora_2': int2_nota,
                'integradora_3': int3_nota,
                'promedio_integradoras': prom_int,
                'porcentaje_integradoras': porc_int,
                'total_bi': nota_data.get('total_bi'),
                'prueba_objetiva': nota_data.get('prueba_objetiva'),
                'porcentaje_po': porc_po,
                'nota_final_periodo': nota_data.get('nota_final'),
                'nota_actitud': nota_data.get('actitud') if nota_data.get('actitud') else None
            })
        
        db.session.commit()
        print("DEBUG - Todas las notas guardadas correctamente")
        
        return jsonify({
            "success": True,
            "mensaje": "Notas guardadas correctamente"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR al guardar notas: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "mensaje": f"Error al guardar las notas: {str(e)}"
        })