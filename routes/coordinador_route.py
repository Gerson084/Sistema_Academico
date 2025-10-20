from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.Secciones import Seccion
from models.Estudiantes import Estudiante
from models.matriculas import Matricula
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo
from models.Periodos import Periodo
from models.Materias import Materia
from models.MateriaSeccion import MateriaSeccion
from models.usuarios import Usuario
from db import db
from sqlalchemy import text
from datetime import datetime

coordinador_bp = Blueprint('coordinador', __name__, template_folder='templates')

@coordinador_bp.route('/dashboard')
def dashboard():
    """Dashboard unificado: muestra secciones coordinadas Y materias asignadas como docente"""
    id_usuario = session.get('user_id')
    
    if not id_usuario:
        return redirect(url_for('auth.login'))
    
    # DEBUG: Imprimir información para verificar
    print(f"\n=== DEBUG DASHBOARD ===")
    print(f"ID Usuario: {id_usuario}")
    print(f"Rol Usuario: {session.get('user_role')}")
    
    # ========== SECCIÓN 1: COORDINADOR ==========
    # Obtener las secciones que coordina
    secciones = Seccion.query.filter_by(
        id_coordinador=id_usuario,
        activo=True
    ).all()
    
    print(f"Secciones encontradas como coordinador: {len(secciones)}")
    
    # Obtener información detallada de cada sección
    secciones_info = []
    for seccion in secciones:
        # Contar estudiantes matriculados
        total_estudiantes = Matricula.query.filter_by(
            id_seccion=seccion.id_seccion,
            activa=True
        ).count()
        
        # Contar materias asignadas
        total_materias = MateriaSeccion.query.filter_by(
            id_seccion=seccion.id_seccion
        ).count()
        
        secciones_info.append({
            'seccion': seccion,
            'total_estudiantes': total_estudiantes,
            'total_materias': total_materias
        })
    
    # ========== SECCIÓN 2: DOCENTE ==========
    # Obtener las materias asignadas como docente
    ano_seleccionado = request.args.get('ano_lectivo', type=int)
    
    print(f"Buscando materias como docente...")
    
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
        'id_docente': id_usuario,
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
    
    # Determinar qué mostrar
    es_coordinador = len(secciones_info) > 0
    es_docente = len(asignaciones) > 0
    
    print(f"Es coordinador: {es_coordinador} ({len(secciones_info)} secciones)")
    print(f"Es docente: {es_docente} ({len(asignaciones)} asignaciones)")
    print(f"======================\n")
    
    return render_template('coordinador/dashboard.html',
                         secciones_info=secciones_info,
                         asignaciones=asignaciones,
                         anos_lectivos=anos_lectivos,
                         ano_seleccionado=ano_seleccionado,
                         es_coordinador=es_coordinador,
                         es_docente=es_docente)


@coordinador_bp.route('/seccion/<int:id_seccion>/estudiantes')
def ver_estudiantes(id_seccion):
    """Ver todos los estudiantes de una sección"""
    id_coordinador = session.get('user_id')
    
    if not id_coordinador:
        return redirect(url_for('auth.login'))
    
    # Verificar que es coordinador de esta sección
    seccion = Seccion.query.filter_by(
        id_seccion=id_seccion,
        id_coordinador=id_coordinador,
        activo=True
    ).first_or_404()
    
    # Obtener información de la sección
    query_info = text("""
        SELECT 
            s.id_seccion,
            s.nombre_seccion,
            g.nombre_grado,
            g.nivel,
            al.ano as ano_lectivo,
            al.id_ano_lectivo
        FROM secciones s
        INNER JOIN grados g ON s.id_grado = g.id_grado
        INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
        WHERE s.id_seccion = :id_seccion
    """)
    
    info_result = db.session.execute(query_info, {'id_seccion': id_seccion}).first()
    
    # Obtener estudiantes de la sección
    query_estudiantes = text("""
        SELECT 
            e.id_estudiante,
            e.nie,
            e.nombres,
            e.apellidos,
            e.fecha_nacimiento,
            mat.id_matricula,
            (SELECT pa.conducta_final 
             FROM promedios_anuales pa 
             WHERE pa.id_promedio_periodo IN (
                 SELECT pp.id_promedio_periodo 
                 FROM promedios_periodo pp
                 INNER JOIN calificaciones c ON pp.id_calificacion = c.id_calificacion
                 WHERE c.id_estudiante = e.id_estudiante
             )
             LIMIT 1) as conducta_final
        FROM estudiantes e
        INNER JOIN matriculas mat ON e.id_estudiante = mat.id_estudiante
        WHERE mat.id_seccion = :id_seccion
        AND mat.activa = 1
        AND e.activo = 1
        ORDER BY e.apellidos, e.nombres
    """)
    
    estudiantes_result = db.session.execute(query_estudiantes, {'id_seccion': id_seccion})
    
    estudiantes = []
    for row in estudiantes_result:
        estudiantes.append({
            'id_estudiante': row.id_estudiante,
            'nie': row.nie,
            'nombre_completo': f"{row.apellidos}, {row.nombres}",
            'fecha_nacimiento': row.fecha_nacimiento,
            'id_matricula': row.id_matricula,
            'conducta_final': row.conducta_final
        })
    
    # Obtener materias de la sección
    query_materias = text("""
        SELECT 
            m.id_materia,
            m.nombre_materia,
            m.codigo_materia,
            ms.id_asignacion,
            u.nombres as nombre_docente,
            u.apellidos as apellido_docente
        FROM materia_seccion ms
        INNER JOIN materias m ON ms.id_materia = m.id_materia
        LEFT JOIN usuarios u ON ms.id_maestro = u.id_usuario
        WHERE ms.id_seccion = :id_seccion
        AND m.activa = 1
        ORDER BY m.nombre_materia
    """)
    
    materias_result = db.session.execute(query_materias, {'id_seccion': id_seccion})
    
    materias = []
    for row in materias_result:
        materias.append({
            'id_materia': row.id_materia,
            'nombre_materia': row.nombre_materia,
            'codigo_materia': row.codigo_materia,
            'id_asignacion': row.id_asignacion,
            'docente': f"{row.apellido_docente}, {row.nombre_docente}" if row.nombre_docente else "Sin asignar"
        })
    
    info_seccion = {
        'id_seccion': info_result.id_seccion,
        'nombre_seccion': info_result.nombre_seccion,
        'grado': f"{info_result.nombre_grado} - {info_result.nivel}",
        'ano_lectivo': info_result.ano_lectivo,
        'id_ano_lectivo': info_result.id_ano_lectivo
    }
    
    return render_template('coordinador/estudiantes_seccion.html',
                         info_seccion=info_seccion,
                         estudiantes=estudiantes,
                         materias=materias)


@coordinador_bp.route('/estudiante/<int:id_estudiante>/notas')
def ver_notas_estudiante(id_estudiante):
    """Ver todas las notas de un estudiante por materia"""
    id_coordinador = session.get('user_id')
    
    if not id_coordinador:
        return redirect(url_for('auth.login'))
    
    # Obtener información del estudiante
    query_estudiante = text("""
        SELECT 
            e.id_estudiante,
            e.nie,
            e.nombres,
            e.apellidos,
            e.fecha_nacimiento,
            mat.id_matricula,
            mat.id_seccion,
            (SELECT pa.conducta_final 
             FROM promedios_anuales pa 
             WHERE pa.id_promedio_periodo IN (
                 SELECT pp.id_promedio_periodo 
                 FROM promedios_periodo pp
                 INNER JOIN calificaciones c ON pp.id_calificacion = c.id_calificacion
                 WHERE c.id_estudiante = e.id_estudiante
             )
             LIMIT 1) as conducta_final,
            s.nombre_seccion,
            g.nombre_grado,
            g.nivel,
            al.ano as ano_lectivo,
            al.id_ano_lectivo
        FROM estudiantes e
        INNER JOIN matriculas mat ON e.id_estudiante = mat.id_estudiante
        INNER JOIN secciones s ON mat.id_seccion = s.id_seccion
        INNER JOIN grados g ON s.id_grado = g.id_grado
        INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
        WHERE e.id_estudiante = :id_estudiante
        AND mat.activa = 1
        AND s.id_coordinador = :id_coordinador
    """)
    
    est_result = db.session.execute(query_estudiante, {
        'id_estudiante': id_estudiante,
        'id_coordinador': id_coordinador
    }).first()
    
    if not est_result:
        return "No tiene permisos para ver este estudiante", 403
    
    # Obtener períodos del año lectivo
    periodos = Periodo.query.filter_by(
        id_ano_lectivo=est_result.id_ano_lectivo
    ).order_by(Periodo.numero_periodo).all()
    
    # Obtener materias y notas del estudiante
    query_notas = text("""
        SELECT 
            m.id_materia,
            m.nombre_materia,
            m.codigo_materia,
            ms.id_asignacion,
            u.nombres as nombre_docente,
            u.apellidos as apellido_docente
        FROM materia_seccion ms
        INNER JOIN materias m ON ms.id_materia = m.id_materia
        LEFT JOIN usuarios u ON ms.id_maestro = u.id_usuario
        WHERE ms.id_seccion = :id_seccion
        AND m.activa = 1
        ORDER BY m.nombre_materia
    """)
    
    materias_result = db.session.execute(query_notas, {'id_seccion': est_result.id_seccion})
    
    # Para cada materia, obtener notas por período
    materias_notas = []
    for mat_row in materias_result:
        # Obtener notas de todos los períodos
        query_notas_periodos = text("""
            SELECT 
                id_periodo,
                nota_final_periodo,
                nota_actitud
            FROM notas_resumen_periodo
            WHERE id_estudiante = :id_estudiante
            AND id_asignacion = :id_asignacion
        """)
        
        notas_result = db.session.execute(query_notas_periodos, {
            'id_estudiante': id_estudiante,
            'id_asignacion': mat_row.id_asignacion
        })
        
        notas_map = {r.id_periodo: {
            'nota': float(r.nota_final_periodo) if r.nota_final_periodo else None,
            'actitud': r.nota_actitud
        } for r in notas_result}
        
        # Construir array de notas por período
        notas_por_periodo = []
        suma_notas = 0
        count_notas = 0
        
        for periodo in periodos:
            nota_data = notas_map.get(periodo.id_periodo)
            if nota_data and nota_data['nota'] is not None:
                notas_por_periodo.append(nota_data['nota'])
                suma_notas += nota_data['nota']
                count_notas += 1
            else:
                notas_por_periodo.append(None)
        
        promedio_anual = round(suma_notas / count_notas, 2) if count_notas > 0 else None
        
        materias_notas.append({
            'id_materia': mat_row.id_materia,
            'nombre_materia': mat_row.nombre_materia,
            'codigo_materia': mat_row.codigo_materia,
            'docente': f"{mat_row.apellido_docente}, {mat_row.nombre_docente}" if mat_row.nombre_docente else "Sin asignar",
            'notas_por_periodo': notas_por_periodo,
            'promedio_anual': promedio_anual
        })
    
    info_estudiante = {
        'id_estudiante': est_result.id_estudiante,
        'nie': est_result.nie,
        'nombre_completo': f"{est_result.apellidos}, {est_result.nombres}",
        'fecha_nacimiento': est_result.fecha_nacimiento,
        'id_matricula': est_result.id_matricula,
        'conducta_final': est_result.conducta_final,
        'seccion': est_result.nombre_seccion,
        'grado': f"{est_result.nombre_grado} - {est_result.nivel}",
        'ano_lectivo': est_result.ano_lectivo,
        'id_seccion': est_result.id_seccion
    }
    
    return render_template('coordinador/notas_estudiante.html',
                         info_estudiante=info_estudiante,
                         materias_notas=materias_notas,
                         periodos=periodos)


@coordinador_bp.route('/estudiante/<int:id_estudiante>/conducta/guardar', methods=['POST'])
def guardar_conducta(id_estudiante):
    """Guardar la conducta final de un estudiante"""
    id_coordinador = session.get('user_id')
    
    if not id_coordinador:
        return jsonify({"success": False, "mensaje": "Sesión expirada"})
    
    try:
        data = request.get_json()
        conducta = data.get('conducta')
        id_matricula = data.get('id_matricula')
        
        if not conducta or not id_matricula:
            return jsonify({"success": False, "mensaje": "Datos incompletos"})
        
        # Verificar que la matrícula pertenece a una sección del coordinador
        query_verificar = text("""
            SELECT m.id_matricula
            FROM matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            WHERE m.id_matricula = :id_matricula
            AND m.id_estudiante = :id_estudiante
            AND s.id_coordinador = :id_coordinador
        """)
        
        verificacion = db.session.execute(query_verificar, {
            'id_matricula': id_matricula,
            'id_estudiante': id_estudiante,
            'id_coordinador': id_coordinador
        }).first()
        
        if not verificacion:
            return jsonify({"success": False, "mensaje": "No tiene permisos para modificar esta conducta"})
        
        # Obtener el id_promedio_periodo del estudiante
        # Primero obtenemos cualquier promedio_periodo del estudiante del año actual
        query_promedio_periodo = text("""
            SELECT pp.id_promedio_periodo
            FROM promedios_periodo pp
            INNER JOIN calificaciones c ON pp.id_calificacion = c.id_calificacion
            WHERE c.id_estudiante = :id_estudiante
            LIMIT 1
        """)
        
        promedio_periodo_result = db.session.execute(query_promedio_periodo, {
            'id_estudiante': id_estudiante
        }).first()
        
        if not promedio_periodo_result:
            return jsonify({"success": False, "mensaje": "No se encontraron calificaciones para este estudiante"})
        
        id_promedio_periodo = promedio_periodo_result[0]
        
        # Verificar si ya existe un registro en promedios_anuales para este estudiante
        query_existe = text("""
            SELECT id_promedio_anual 
            FROM promedios_anuales 
            WHERE id_promedio_periodo = :id_promedio_periodo
        """)
        
        registro_existente = db.session.execute(query_existe, {
            'id_promedio_periodo': id_promedio_periodo
        }).first()
        
        if registro_existente:
            # Actualizar conducta en registro existente
            update_conducta = text("""
                UPDATE promedios_anuales
                SET conducta_final = :conducta
                WHERE id_promedio_periodo = :id_promedio_periodo
            """)
            
            db.session.execute(update_conducta, {
                'conducta': conducta,
                'id_promedio_periodo': id_promedio_periodo
            })
        else:
            # Crear nuevo registro en promedios_anuales
            # Necesitamos obtener el id_periodo actual
            query_periodo = text("""
                SELECT p.id_periodo
                FROM periodos p
                INNER JOIN secciones s ON p.id_ano_lectivo = s.id_ano_lectivo
                INNER JOIN matriculas m ON s.id_seccion = m.id_seccion
                WHERE m.id_matricula = :id_matricula
                ORDER BY p.numero_periodo DESC
                LIMIT 1
            """)
            
            periodo_result = db.session.execute(query_periodo, {
                'id_matricula': id_matricula
            }).first()
            
            if periodo_result:
                insert_conducta = text("""
                    INSERT INTO promedios_anuales 
                    (id_promedio_periodo, id_periodo, conducta_final, estado_final)
                    VALUES (:id_promedio_periodo, :id_periodo, :conducta, 'Pendiente')
                """)
                
                db.session.execute(insert_conducta, {
                    'id_promedio_periodo': id_promedio_periodo,
                    'id_periodo': periodo_result[0],
                    'conducta': conducta
                })
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "mensaje": "Conducta guardada correctamente"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR al guardar conducta: {str(e)}")
        return jsonify({
            "success": False,
            "mensaje": f"Error al guardar la conducta: {str(e)}"
        })
