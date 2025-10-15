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
        estudiantes.append({
            'id_estudiante': row.id_estudiante,
            'nie': row.nie,
            'nombre_completo': f"{row.apellidos}, {row.nombres}",
            'id_matricula': row.id_matricula
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
        notas = data.get('notas', [])
        
        if not id_periodo:
            return jsonify({"success": False, "mensaje": "Debe seleccionar un período"})
        
        # Procesar cada estudiante
        for nota_data in notas:
            id_estudiante = nota_data.get('id_estudiante')
            
            # Aquí debes implementar la lógica según tu estructura de calificaciones
            # Este es un ejemplo básico
            
            # Guardar actividades
            act1 = nota_data.get('act1')
            act2 = nota_data.get('act2')
            act3 = nota_data.get('act3')
            
            # Guardar nota de RC
            nota_rc = nota_data.get('nota_rc')
            
            # Guardar integradoras
            int1 = nota_data.get('int1')
            int2 = nota_data.get('int2')
            int3 = nota_data.get('int3')
            
            # Guardar prueba objetiva
            prueba_obj = nota_data.get('prueba_obj')
            
            # Actitud
            actitud = nota_data.get('actitud')
            
            # Aquí debes implementar el guardado según tu modelo de datos
            # Por ejemplo, crear registros en la tabla calificaciones
            
        db.session.commit()
        
        return jsonify({
            "success": True,
            "mensaje": "Notas guardadas correctamente"
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar notas: {str(e)}")
        return jsonify({
            "success": False,
            "mensaje": f"Error al guardar las notas: {str(e)}"
        })