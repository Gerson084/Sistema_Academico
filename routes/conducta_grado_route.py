from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from db.cn import db
from sqlalchemy import text
from models.ConductaGrado import ConductaGradoPeriodo
from models.Secciones import Seccion
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo

conducta_grado_bp = Blueprint('conducta_grado', __name__, url_prefix='/conducta-grado')

@conducta_grado_bp.route('/grados')
def listar_grados():
    """Muestra la lista de grados disponibles para ingresar conducta"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Permitir: 1=Admin, 2=Docente, 3=Coordinador
    if not user_id or user_role not in [1, 2, 3]:
        return redirect(url_for('auth.login'))
    
    # Obtener año lectivo activo
    ano_activo = AnoLectivo.query.filter_by(activo=1).first()
    
    if not ano_activo:
        return render_template('conducta_grado/lista_grados.html',
                             grados=[],
                             ano_lectivo=None,
                             mensaje="No hay año lectivo activo")
    
    # Obtener todos los grados con secciones del año activo
    query = text("""
        SELECT 
            g.id_grado,
            g.nombre_grado,
            g.nivel,
            COUNT(DISTINCT s.id_seccion) as total_secciones,
            COUNT(DISTINCT m.id_estudiante) as total_estudiantes
        FROM grados g
        LEFT JOIN secciones s ON g.id_grado = s.id_grado 
            AND s.id_ano_lectivo = :id_ano_lectivo
        LEFT JOIN matriculas m ON s.id_seccion = m.id_seccion 
            AND m.activa = 1
        WHERE g.activo = 1
        GROUP BY g.id_grado, g.nombre_grado, g.nivel
        ORDER BY g.nivel, g.nombre_grado
    """)
    
    result = db.session.execute(query, {'id_ano_lectivo': ano_activo.id_ano_lectivo})
    
    grados = []
    for row in result:
        grados.append({
            'id_grado': row.id_grado,
            'nombre_grado': row.nombre_grado,
            'nivel': row.nivel,
            'total_secciones': row.total_secciones or 0,
            'total_estudiantes': row.total_estudiantes or 0
        })
    
    return render_template('conducta_grado/lista_grados.html',
                         grados=grados,
                         ano_lectivo=ano_activo)


@conducta_grado_bp.route('/secciones/<int:id_grado>')
def listar_secciones(id_grado):
    """Muestra las secciones de un grado específico"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Permitir: 1=Admin, 2=Docente, 3=Coordinador
    if not user_id or user_role not in [1, 2, 3]:
        return redirect(url_for('auth.login'))
    
    # Obtener año lectivo activo
    ano_activo = AnoLectivo.query.filter_by(activo=1).first()
    
    if not ano_activo:
        return redirect(url_for('conducta_grado.listar_grados'))
    
    # Obtener información del grado
    grado = Grado.query.filter_by(id_grado=id_grado, activo=1).first_or_404()
    
    # Obtener secciones del grado en el año activo
    query = text("""
        SELECT 
            s.id_seccion,
            s.nombre_seccion,
            COUNT(DISTINCT m.id_estudiante) as total_estudiantes,
            COUNT(DISTINCT cgp.id_conducta_grado) as total_conductas
        FROM secciones s
        LEFT JOIN matriculas m ON s.id_seccion = m.id_seccion AND m.activa = 1
        LEFT JOIN conducta_grado_periodo cgp ON s.id_seccion = cgp.id_seccion 
            AND cgp.id_ano_lectivo = :id_ano_lectivo
        WHERE s.id_grado = :id_grado 
            AND s.id_ano_lectivo = :id_ano_lectivo
        GROUP BY s.id_seccion, s.nombre_seccion
        ORDER BY s.nombre_seccion
    """)
    
    result = db.session.execute(query, {
        'id_grado': id_grado,
        'id_ano_lectivo': ano_activo.id_ano_lectivo
    })
    
    secciones = []
    for row in result:
        total_est = row.total_estudiantes or 0
        total_cond = row.total_conductas or 0
        porcentaje = int((total_cond / total_est * 100)) if total_est > 0 else 0
        
        secciones.append({
            'id_seccion': row.id_seccion,
            'nombre_seccion': row.nombre_seccion,
            'total_estudiantes': total_est,
            'total_conductas': total_cond,
            'porcentaje': porcentaje
        })
    
    return render_template('conducta_grado/lista_secciones.html',
                         grado=grado,
                         secciones=secciones,
                         ano_lectivo=ano_activo)


@conducta_grado_bp.route('/ingresar/<int:id_seccion>')
def ingresar_conducta(id_seccion):
    """Muestra el formulario para ingresar conducta final de estudiantes"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Permitir: 1=Admin, 2=Docente, 3=Coordinador
    if not user_id or user_role not in [1, 2, 3]:
        return redirect(url_for('auth.login'))
    
    # Obtener año lectivo activo
    ano_activo = AnoLectivo.query.filter_by(activo=1).first()
    
    if not ano_activo:
        return redirect(url_for('conducta_grado.listar_grados'))
    
    # Obtener información de la sección
    query_seccion = text("""
        SELECT 
            s.id_seccion,
            s.nombre_seccion,
            g.nombre_grado,
            g.nivel,
            g.id_grado,
            al.ano
        FROM secciones s
        INNER JOIN grados g ON s.id_grado = g.id_grado
        INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
        WHERE s.id_seccion = :id_seccion
    """)
    
    info_seccion = db.session.execute(query_seccion, {'id_seccion': id_seccion}).first()
    
    if not info_seccion:
        return redirect(url_for('conducta_grado.listar_grados'))
    
    # Obtener estudiantes matriculados con su conducta existente
    query_estudiantes = text("""
        SELECT 
            e.id_estudiante,
            e.nie,
            e.nombres,
            e.apellidos,
            cgp.nota_conducta_final,
            cgp.conducta_literal,
            cgp.observacion_general
        FROM estudiantes e
        INNER JOIN matriculas m ON e.id_estudiante = m.id_estudiante
        LEFT JOIN conducta_grado_periodo cgp ON e.id_estudiante = cgp.id_estudiante 
            AND cgp.id_seccion = :id_seccion
            AND cgp.id_ano_lectivo = :id_ano_lectivo
        WHERE m.id_seccion = :id_seccion
            AND m.activa = 1
            AND e.activo = 1
        ORDER BY e.apellidos, e.nombres
    """)
    
    result = db.session.execute(query_estudiantes, {
        'id_seccion': id_seccion,
        'id_ano_lectivo': ano_activo.id_ano_lectivo
    })
    
    estudiantes = []
    for row in result:
        estudiantes.append({
            'id_estudiante': row.id_estudiante,
            'nie': row.nie,
            'nombre_completo': f"{row.apellidos}, {row.nombres}",
            'nota_conducta': float(row.nota_conducta_final) if row.nota_conducta_final else None,
            'conducta_literal': row.conducta_literal,
            'observacion': row.observacion_general
        })
    
    info = {
        'id_seccion': info_seccion.id_seccion,
        'nombre_seccion': info_seccion.nombre_seccion,
        'grado': f"{info_seccion.nombre_grado} - {info_seccion.nivel}",
        'id_grado': info_seccion.id_grado,
        'ano_lectivo': info_seccion.ano
    }
    
    return render_template('conducta_grado/ingresar_conducta.html',
                         info_seccion=info,
                         estudiantes=estudiantes,
                         ano_lectivo=ano_activo)


@conducta_grado_bp.route('/guardar', methods=['POST'])
def guardar_conducta():
    """Guarda la conducta final de los estudiantes"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Permitir: 1=Admin, 2=Docente, 3=Coordinador
    if not user_id or user_role not in [1, 2, 3]:
        return jsonify({'success': False, 'mensaje': 'No autorizado'}), 403
    
    try:
        data = request.get_json()
        id_seccion = data.get('id_seccion')
        id_ano_lectivo = data.get('id_ano_lectivo')
        conductas = data.get('conductas', [])
        
        if not id_seccion or not id_ano_lectivo:
            return jsonify({'success': False, 'mensaje': 'Datos incompletos'}), 400
        
        if not conductas:
            return jsonify({'success': False, 'mensaje': 'No hay conductas para guardar'}), 400
        
        # Procesar cada estudiante
        guardados = 0
        for conducta in conductas:
            id_estudiante = conducta.get('id_estudiante')
            tipo_conducta = conducta.get('tipo_conducta')  # 'numerica' o 'literal'
            nota_numerica = conducta.get('nota_numerica')
            conducta_literal = conducta.get('conducta_literal')
            observacion = conducta.get('observacion', '').strip() or None
            
            # Validar que tenga al menos una conducta
            if not nota_numerica and not conducta_literal:
                continue
            
            # Validar tipo de conducta
            if tipo_conducta == 'numerica':
                if nota_numerica is not None:
                    nota_numerica = float(nota_numerica)
                    if nota_numerica < 0 or nota_numerica > 10:
                        return jsonify({
                            'success': False,
                            'mensaje': f'La nota numérica debe estar entre 0 y 10 (Estudiante ID: {id_estudiante})'
                        }), 400
                    conducta_literal_val = None
                else:
                    continue
            else:  # literal
                if conducta_literal and conducta_literal in ['E', 'MB', 'B', 'R', 'NM']:
                    conducta_literal_val = conducta_literal
                    nota_numerica = None
                else:
                    continue
            
            # Usar ON DUPLICATE KEY UPDATE
            query = text("""
                INSERT INTO conducta_grado_periodo 
                    (id_estudiante, id_seccion, id_ano_lectivo, nota_conducta_final, 
                     conducta_literal, observacion_general)
                VALUES 
                    (:id_estudiante, :id_seccion, :id_ano_lectivo, :nota_conducta, 
                     :conducta_literal, :observacion)
                ON DUPLICATE KEY UPDATE
                    nota_conducta_final = VALUES(nota_conducta_final),
                    conducta_literal = VALUES(conducta_literal),
                    observacion_general = VALUES(observacion_general),
                    fecha_modificacion = CURRENT_TIMESTAMP
            """)
            
            db.session.execute(query, {
                'id_estudiante': id_estudiante,
                'id_seccion': id_seccion,
                'id_ano_lectivo': id_ano_lectivo,
                'nota_conducta': nota_numerica,
                'conducta_literal': conducta_literal_val,
                'observacion': observacion
            })
            guardados += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Se guardaron {guardados} conducta(s) exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar conductas: {e}")
        return jsonify({
            'success': False,
            'mensaje': f'Error al guardar: {str(e)}'
        }), 500
