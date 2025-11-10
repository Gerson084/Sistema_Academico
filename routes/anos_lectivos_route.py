from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from db.cn import db
from sqlalchemy import text
from models.AnosLectivos import AnoLectivo
from datetime import datetime

anos_lectivos_bp = Blueprint('anos_lectivos', __name__, url_prefix='/anos-lectivos')

@anos_lectivos_bp.route('/')
def listar_anos():
    """Lista todos los años lectivos"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Solo Admin
    if not user_id or user_role != 1:
        flash('Acceso denegado. Solo administradores.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Obtener todos los años lectivos
    anos = AnoLectivo.query.order_by(AnoLectivo.ano.desc()).all()
    
    # Obtener estadísticas de cada año
    anos_data = []
    for ano in anos:
        # Contar secciones
        query_secciones = text("""
            SELECT COUNT(*) as total
            FROM secciones 
            WHERE id_ano_lectivo = :id_ano
        """)
        total_secciones = db.session.execute(query_secciones, {'id_ano': ano.id_ano_lectivo}).scalar()
        
        # Contar estudiantes matriculados
        query_estudiantes = text("""
            SELECT COUNT(DISTINCT m.id_estudiante) as total
            FROM matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            WHERE s.id_ano_lectivo = :id_ano AND m.activa = 1
        """)
        total_estudiantes = db.session.execute(query_estudiantes, {'id_ano': ano.id_ano_lectivo}).scalar()
        
        # Contar periodos
        query_periodos = text("""
            SELECT COUNT(*) as total
            FROM periodos 
            WHERE id_ano_lectivo = :id_ano
        """)
        total_periodos = db.session.execute(query_periodos, {'id_ano': ano.id_ano_lectivo}).scalar()
        
        anos_data.append({
            'ano': ano,
            'total_secciones': total_secciones or 0,
            'total_estudiantes': total_estudiantes or 0,
            'total_periodos': total_periodos or 0
        })
    
    return render_template('anos_lectivos/lista.html', anos=anos_data)


@anos_lectivos_bp.route('/crear', methods=['GET', 'POST'])
def crear_ano():
    """Crear nuevo año lectivo"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            ano = int(data.get('ano'))
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            
            # ===== VALIDACIONES =====
            
            # Obtener año actual para validaciones dinámicas
            from datetime import date as date_class
            ano_actual = date_class.today().year
            ano_minimo = 2020  # Año mínimo histórico del sistema
            ano_maximo = ano_actual + 5  # Permitir planificar hasta 5 años en el futuro
            
            # 1. Validar año en rango dinámico
            if ano < ano_minimo or ano > ano_maximo:
                return jsonify({
                    'success': False,
                    'mensaje': f'El año {ano} está fuera del rango válido ({ano_minimo}-{ano_maximo})'
                })
            
            # 2. Convertir fechas
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'mensaje': 'Formato de fecha inválido. Use YYYY-MM-DD'
                })
            
            # 3. Validar años de las fechas
            if fecha_inicio_date.year < ano_minimo or fecha_inicio_date.year > ano_maximo:
                return jsonify({
                    'success': False,
                    'mensaje': f'La fecha de inicio ({fecha_inicio_date.year}) está fuera del rango válido ({ano_minimo}-{ano_maximo})'
                })
            
            if fecha_fin_date.year < ano_minimo or fecha_fin_date.year > ano_maximo:
                return jsonify({
                    'success': False,
                    'mensaje': f'La fecha de fin ({fecha_fin_date.year}) está fuera del rango válido ({ano_minimo}-{ano_maximo})'
                })
            
            # 4. Validar que fecha_fin > fecha_inicio
            if fecha_fin_date <= fecha_inicio_date:
                return jsonify({
                    'success': False,
                    'mensaje': 'La fecha de fin debe ser posterior a la fecha de inicio'
                })
            
            # 5. Validar coherencia: las fechas deben estar cerca del año lectivo
            if abs(fecha_inicio_date.year - ano) > 1:
                return jsonify({
                    'success': False,
                    'mensaje': f'La fecha de inicio ({fecha_inicio_date.year}) no corresponde al año lectivo {ano}'
                })
            
            # 6. Verificar si ya existe
            existe = AnoLectivo.query.filter_by(ano=ano).first()
            if existe:
                return jsonify({'success': False, 'mensaje': f'El año {ano} ya existe'})
            
            # Crear nuevo año
            nuevo_ano = AnoLectivo(
                ano=ano,
                fecha_inicio=fecha_inicio_date,
                fecha_fin=fecha_fin_date,
                activo=False  # Inicia inactivo
            )
            
            db.session.add(nuevo_ano)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'mensaje': f'Año lectivo {ano} creado exitosamente',
                'id_ano_lectivo': nuevo_ano.id_ano_lectivo
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'mensaje': f'Error: {str(e)}'})
    
    return render_template('anos_lectivos/crear.html')


@anos_lectivos_bp.route('/editar/<int:id_ano>', methods=['GET', 'POST'])
def editar_ano(id_ano):
    """Editar año lectivo (solo si está inactivo y sin matrículas)"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        if request.method == 'POST':
            return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
        flash('Acceso denegado', 'danger')
        return redirect(url_for('auth.login'))
    
    ano = AnoLectivo.query.get_or_404(id_ano)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            nuevo_ano = int(data.get('ano'))
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            
            # ===== VALIDACIONES PREVIAS =====
            
            # Validar que el año esté inactivo
            if ano.activo:
                return jsonify({
                    'success': False,
                    'mensaje': 'No se puede editar un año activo. Desactívalo primero.'
                })
            
            # Validar que no tenga matrículas
            query_matriculas = text("""
                SELECT COUNT(*) FROM matriculas m
                INNER JOIN secciones s ON m.id_seccion = s.id_seccion
                WHERE s.id_ano_lectivo = :id_ano
            """)
            total_matriculas = db.session.execute(query_matriculas, {'id_ano': id_ano}).scalar()
            
            if total_matriculas > 0:
                return jsonify({
                    'success': False,
                    'mensaje': f'No se puede editar porque el año {ano.ano} tiene {total_matriculas} matrículas registradas.'
                })
            
            # ===== VALIDACIONES DE DATOS =====
            
            # Obtener año actual para validaciones dinámicas
            from datetime import date as date_class
            ano_actual = date_class.today().year
            ano_minimo = 2020  # Año mínimo histórico del sistema
            ano_maximo = ano_actual + 5  # Permitir planificar hasta 5 años en el futuro
            
            # 1. Validar año en rango dinámico
            if nuevo_ano < ano_minimo or nuevo_ano > ano_maximo:
                return jsonify({
                    'success': False,
                    'mensaje': f'El año {nuevo_ano} está fuera del rango válido ({ano_minimo}-{ano_maximo})'
                })
            
            # 2. Convertir fechas
            try:
                fecha_inicio_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'mensaje': 'Formato de fecha inválido. Use YYYY-MM-DD'
                })
            
            # 3. Validar años de las fechas
            if fecha_inicio_date.year < ano_minimo or fecha_inicio_date.year > ano_maximo:
                return jsonify({
                    'success': False,
                    'mensaje': f'La fecha de inicio ({fecha_inicio_date.year}) está fuera del rango válido ({ano_minimo}-{ano_maximo})'
                })
            
            if fecha_fin_date.year < ano_minimo or fecha_fin_date.year > ano_maximo:
                return jsonify({
                    'success': False,
                    'mensaje': f'La fecha de fin ({fecha_fin_date.year}) está fuera del rango válido ({ano_minimo}-{ano_maximo})'
                })
            
            # 4. Validar que fecha_fin > fecha_inicio
            if fecha_fin_date <= fecha_inicio_date:
                return jsonify({
                    'success': False,
                    'mensaje': 'La fecha de fin debe ser posterior a la fecha de inicio'
                })
            
            # 5. Validar coherencia: las fechas deben estar cerca del año lectivo
            if abs(fecha_inicio_date.year - nuevo_ano) > 1:
                return jsonify({
                    'success': False,
                    'mensaje': f'La fecha de inicio ({fecha_inicio_date.year}) no corresponde al año lectivo {nuevo_ano}'
                })
            
            # 6. Verificar que el nuevo año no exista (si cambió)
            if nuevo_ano != ano.ano:
                existe = AnoLectivo.query.filter_by(ano=nuevo_ano).first()
                if existe:
                    return jsonify({'success': False, 'mensaje': f'El año {nuevo_ano} ya existe'})
            
            # Actualizar año
            ano.ano = nuevo_ano
            ano.fecha_inicio = fecha_inicio_date
            ano.fecha_fin = fecha_fin_date
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'mensaje': f'Año lectivo actualizado correctamente',
                'redirect': url_for('anos_lectivos.listar_anos')
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'mensaje': f'Error: {str(e)}'})
    
    # GET: Mostrar formulario
    return render_template('anos_lectivos/editar.html', ano=ano)


@anos_lectivos_bp.route('/activar/<int:id_ano>', methods=['POST'])
def activar_ano(id_ano):
    """Activar un año lectivo (desactiva los demás)"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
    
    try:
        ano = AnoLectivo.query.get(id_ano)
        if not ano:
            return jsonify({'success': False, 'mensaje': 'Año no encontrado'})
        
        # ===== VALIDACIONES ANTES DE ACTIVAR =====
        
        # 0. Verificar si ya hay un año activo
        ano_activo_actual = AnoLectivo.query.filter_by(activo=True).first()
        if ano_activo_actual and ano_activo_actual.id_ano_lectivo != id_ano:
            return jsonify({
                'success': False,
                'mensaje': f'Ya existe un año lectivo activo ({ano_activo_actual.ano}). Primero desactívalo antes de activar otro.',
                'ano_activo': ano_activo_actual.ano
            })
        
        # Si el año ya está activo, no hacer nada
        if ano.activo:
            return jsonify({
                'success': True,
                'mensaje': f'El año {ano.ano} ya está activo.'
            })
        
        # 1. Verificar que tenga períodos
        query_periodos = text("SELECT COUNT(*) FROM periodos WHERE id_ano_lectivo = :id_ano")
        total_periodos = db.session.execute(query_periodos, {'id_ano': id_ano}).scalar()
        
        if total_periodos == 0:
            return jsonify({
                'success': False,
                'mensaje': f'No se puede activar el año {ano.ano} porque no tiene períodos académicos. Créalos primero.'
            })
        
        if total_periodos < 4:
            return jsonify({
                'success': False,
                'mensaje': f'El año {ano.ano} solo tiene {total_periodos} períodos. Se requieren 4 períodos académicos.'
            })
        
        # ===== ACTIVAR AÑO =====
        
        # Desactivar todos los años
        AnoLectivo.query.update({'activo': False})
        
        # Desactivar todos los períodos de todos los años
        query_desactivar_periodos = text("UPDATE periodos SET activo = 0")
        db.session.execute(query_desactivar_periodos)
        
        # Activar el año seleccionado
        ano.activo = True
        
        # Activar los períodos del año seleccionado
        query_activar_periodos = text("""
            UPDATE periodos 
            SET activo = 1 
            WHERE id_ano_lectivo = :id_ano
        """)
        db.session.execute(query_activar_periodos, {'id_ano': id_ano})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Año lectivo {ano.ano} activado correctamente. Se activaron {total_periodos} períodos.',
            'redirect': url_for('anos_lectivos.listar_anos')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'mensaje': f'Error: {str(e)}'})


@anos_lectivos_bp.route('/configurar/<int:id_ano>')
def configurar_ano(id_ano):
    """Configurar períodos y crear secciones para el año lectivo"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('auth.login'))
    
    ano = AnoLectivo.query.get_or_404(id_ano)
    
    # Verificar si ya tiene períodos
    query_periodos = text("SELECT COUNT(*) FROM periodos WHERE id_ano_lectivo = :id_ano")
    tiene_periodos = db.session.execute(query_periodos, {'id_ano': id_ano}).scalar() > 0
    
    # Obtener total de períodos
    total_periodos = db.session.execute(query_periodos, {'id_ano': id_ano}).scalar() if tiene_periodos else 0
    
    # Verificar si ya tiene secciones
    query_secciones = text("SELECT COUNT(*) FROM secciones WHERE id_ano_lectivo = :id_ano")
    tiene_secciones = db.session.execute(query_secciones, {'id_ano': id_ano}).scalar() > 0
    
    # Obtener total de secciones
    total_secciones = db.session.execute(query_secciones, {'id_ano': id_ano}).scalar() if tiene_secciones else 0
    
    return render_template('anos_lectivos/configurar.html', 
                         ano=ano,
                         tiene_periodos=tiene_periodos,
                         total_periodos=total_periodos,
                         tiene_secciones=tiene_secciones,
                         total_secciones=total_secciones)


@anos_lectivos_bp.route('/crear-periodos/<int:id_ano>', methods=['POST'])
def crear_periodos(id_ano):
    """Crear los 4 períodos para el año lectivo"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
    
    try:
        data = request.get_json()
        periodos = data.get('periodos', [])
        
        for periodo in periodos:
            query = text("""
                INSERT INTO periodos (id_ano_lectivo, numero_periodo, nombre_periodo, fecha_inicio, fecha_fin, activo)
                VALUES (:id_ano, :numero, :nombre, :fecha_inicio, :fecha_fin, 0)
            """)
            
            db.session.execute(query, {
                'id_ano': id_ano,
                'numero': periodo['numero'],
                'nombre': periodo['nombre'],
                'fecha_inicio': periodo['fecha_inicio'],
                'fecha_fin': periodo['fecha_fin']
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'{len(periodos)} períodos creados exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'mensaje': f'Error: {str(e)}'})


@anos_lectivos_bp.route('/obtener-periodos/<int:id_ano>', methods=['GET'])
def obtener_periodos(id_ano):
    """Obtener los períodos de un año lectivo"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
    
    try:
        query = text("""
            SELECT id_periodo, numero_periodo, nombre_periodo, fecha_inicio, fecha_fin
            FROM periodos
            WHERE id_ano_lectivo = :id_ano
            ORDER BY numero_periodo
        """)
        
        result = db.session.execute(query, {'id_ano': id_ano})
        periodos = []
        
        for row in result:
            periodos.append({
                'id_periodo': row.id_periodo,
                'numero_periodo': row.numero_periodo,
                'nombre_periodo': row.nombre_periodo,
                'fecha_inicio': str(row.fecha_inicio),
                'fecha_fin': str(row.fecha_fin)
            })
        
        return jsonify({
            'success': True,
            'periodos': periodos
        })
        
    except Exception as e:
        return jsonify({'success': False, 'mensaje': f'Error: {str(e)}'})


@anos_lectivos_bp.route('/actualizar-periodos/<int:id_ano>', methods=['POST'])
def actualizar_periodos(id_ano):
    """Actualizar los períodos de un año lectivo"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
    
    try:
        data = request.get_json()
        periodos = data.get('periodos', [])
        
        for periodo in periodos:
            query = text("""
                UPDATE periodos 
                SET fecha_inicio = :fecha_inicio, fecha_fin = :fecha_fin
                WHERE id_periodo = :id_periodo
            """)
            
            db.session.execute(query, {
                'id_periodo': periodo['id_periodo'],
                'fecha_inicio': periodo['fecha_inicio'],
                'fecha_fin': periodo['fecha_fin']
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Períodos actualizados exitosamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'mensaje': f'Error: {str(e)}'})


@anos_lectivos_bp.route('/cerrar-ano/<int:id_ano>', methods=['POST'])
def cerrar_ano(id_ano):
    """Cerrar año lectivo: verificar estados y desactivar matrículas"""
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    if not user_id or user_role != 1:
        return jsonify({'success': False, 'mensaje': 'Acceso denegado'}), 403
    
    try:
        ano_actual = AnoLectivo.query.get(id_ano)
        
        if not ano_actual:
            return jsonify({'success': False, 'mensaje': 'Año lectivo no encontrado'})
        
        # ===== VALIDACIÓN 1: Verificar que todos los estudiantes tengan estado final =====
        # El estado_final está en promedios_anuales
        # Ruta: matriculas -> estudiante -> calificaciones -> promedios_periodo -> promedios_anuales
        query_sin_estado = text("""
            SELECT COUNT(DISTINCT m.id_matricula) 
            FROM matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            LEFT JOIN (
                SELECT DISTINCT c.id_estudiante, pa.estado_final
                FROM calificaciones c
                INNER JOIN periodos p ON c.id_periodo = p.id_periodo
                INNER JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
                INNER JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
                WHERE p.id_ano_lectivo = :id_ano
            ) estados ON estados.id_estudiante = m.id_estudiante
            WHERE s.id_ano_lectivo = :id_ano
            AND m.activa = 1
            AND (estados.estado_final IS NULL OR estados.estado_final = 'Pendiente')
        """)
        
        estudiantes_sin_estado = db.session.execute(query_sin_estado, {'id_ano': id_ano}).scalar()
        
        if estudiantes_sin_estado > 0:
            return jsonify({
                'success': False,
                'mensaje': f'No se puede cerrar el año. Hay {estudiantes_sin_estado} estudiantes sin estado final (Aprobado/Reprobado). Por favor, completa todos los estados antes de cerrar el año.'
            })
        
        # ===== VALIDACIÓN 2: Obtener estadísticas del año =====
        query_estadisticas = text("""
            SELECT 
                COUNT(DISTINCT m.id_matricula) as total_matriculas,
                SUM(CASE WHEN estados.estado_final = 'Aprobado' THEN 1 ELSE 0 END) as aprobados,
                SUM(CASE WHEN estados.estado_final = 'Reprobado' THEN 1 ELSE 0 END) as reprobados
            FROM matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            LEFT JOIN (
                SELECT DISTINCT c.id_estudiante, pa.estado_final
                FROM calificaciones c
                INNER JOIN periodos p ON c.id_periodo = p.id_periodo
                INNER JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
                INNER JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
                WHERE p.id_ano_lectivo = :id_ano
            ) estados ON estados.id_estudiante = m.id_estudiante
            WHERE s.id_ano_lectivo = :id_ano
            AND m.activa = 1
        """)
        
        estadisticas = db.session.execute(query_estadisticas, {'id_ano': id_ano}).fetchone()
        
        # ===== VALIDACIÓN 3: Verificar que el año esté activo =====
        if not ano_actual.activo:
            return jsonify({
                'success': False,
                'mensaje': 'Solo se puede cerrar un año lectivo activo'
            })
        
        # ===== PROCESO DE CIERRE =====
        
        # 1. Desactivar todas las matrículas del año
        query_desactivar_matriculas = text("""
            UPDATE matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            SET m.activa = 0
            WHERE s.id_ano_lectivo = :id_ano
        """)
        
        db.session.execute(query_desactivar_matriculas, {'id_ano': id_ano})
        
        # 2. Desactivar los períodos del año
        query_desactivar_periodos = text("""
            UPDATE periodos 
            SET activo = 0 
            WHERE id_ano_lectivo = :id_ano
        """)
        
        db.session.execute(query_desactivar_periodos, {'id_ano': id_ano})
        
        # 3. Desactivar el año lectivo
        ano_actual.activo = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Año lectivo {ano_actual.ano} cerrado exitosamente',
            'estadisticas': {
                'total_matriculas': estadisticas.total_matriculas or 0,
                'aprobados': estadisticas.aprobados or 0,
                'reprobados': estadisticas.reprobados or 0
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'mensaje': f'Error al cerrar año: {str(e)}'})
