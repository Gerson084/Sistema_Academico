from flask import Blueprint, render_template, request, jsonify, url_for
from models.Estudiantes import Estudiante
from models.Secciones import Seccion
from models.matriculas import Matricula
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo
from sqlalchemy import text
from db import db
from datetime import datetime

# Blueprint para matrículas
matriculas_bp = Blueprint('matricula', __name__, template_folder="templates")

# LISTAR MATRÍCULAS - Filtrado por año activo
@matriculas_bp.route("/")
def lista_matriculas():
    try:
        # Obtener parámetro de año (si viene del filtro)
        ano_filtro = request.args.get('ano_lectivo', None)
        
        # Obtener año activo
        ano_activo = AnoLectivo.query.filter_by(activo=True).first()
        
        # Si no se especifica filtro, usar año activo
        if not ano_filtro and ano_activo:
            ano_filtro = ano_activo.id_ano_lectivo
        
        # Consulta SQL filtrando por año lectivo
        if ano_filtro:
            query = text("""
                SELECT 
                    m.id_matricula,
                    m.id_estudiante,
                    m.id_seccion,
                    m.fecha_matricula,
                    m.activa as matricula_activa,
                    estados.estado_final,
                    e.nombres as estudiante_nombres,
                    e.apellidos as estudiante_apellidos,
                    e.nie as estudiante_nie,
                    s.nombre_seccion,
                    g.nombre_grado,
                    g.nivel as grado_nivel,
                    al.ano as ano_lectivo,
                    al.id_ano_lectivo,
                    al.activo as ano_activo,
                    al.fecha_inicio,
                    al.fecha_fin
                FROM matriculas m
                JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
                JOIN secciones s ON m.id_seccion = s.id_seccion
                JOIN grados g ON s.id_grado = g.id_grado
                JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
                LEFT JOIN (
                    SELECT DISTINCT c.id_estudiante, pa.estado_final
                    FROM calificaciones c
                    INNER JOIN periodos p ON c.id_periodo = p.id_periodo
                    INNER JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
                    INNER JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
                    WHERE p.id_ano_lectivo = :ano_filtro
                ) estados ON estados.id_estudiante = m.id_estudiante
                WHERE s.id_ano_lectivo = :ano_filtro
                ORDER BY m.activa DESC, al.ano DESC, m.id_matricula DESC
            """)
            result = db.session.execute(query, {'ano_filtro': ano_filtro})
        else:
            # Si no hay año activo, mostrar todas las matrículas
            query = text("""
                SELECT 
                    m.id_matricula,
                    m.id_estudiante,
                    m.id_seccion,
                    m.fecha_matricula,
                    m.activa as matricula_activa,
                    estados.estado_final,
                    e.nombres as estudiante_nombres,
                    e.apellidos as estudiante_apellidos,
                    e.nie as estudiante_nie,
                    s.nombre_seccion,
                    g.nombre_grado,
                    g.nivel as grado_nivel,
                    al.ano as ano_lectivo,
                    al.id_ano_lectivo,
                    al.activo as ano_activo,
                    al.fecha_inicio,
                    al.fecha_fin
                FROM matriculas m
                JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
                JOIN secciones s ON m.id_seccion = s.id_seccion
                JOIN grados g ON s.id_grado = g.id_grado
                JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
                LEFT JOIN (
                    SELECT DISTINCT c.id_estudiante, pa.estado_final, p.id_ano_lectivo
                    FROM calificaciones c
                    INNER JOIN periodos p ON c.id_periodo = p.id_periodo
                    INNER JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
                    INNER JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
                ) estados ON estados.id_estudiante = m.id_estudiante AND estados.id_ano_lectivo = al.id_ano_lectivo
                ORDER BY m.activa DESC, al.ano DESC, m.id_matricula DESC
            """)
            result = db.session.execute(query)
        
        # Convertir resultado a lista de diccionarios
        matriculas_data = []
        for row in result:
            matriculas_data.append({
                'id_matricula': row.id_matricula,
                'id_estudiante': row.id_estudiante,
                'id_seccion': row.id_seccion,
                'fecha_matricula': row.fecha_matricula,
                'matricula_activa': row.matricula_activa,
                'estado_final': row.estado_final,
                'estudiante_nombres': row.estudiante_nombres,
                'estudiante_apellidos': row.estudiante_apellidos,
                'estudiante_nie': row.estudiante_nie,
                'nombre_seccion': row.nombre_seccion,
                'nombre_grado': row.nombre_grado,
                'grado_nivel': row.grado_nivel,
                'ano_lectivo': row.ano_lectivo,
                'id_ano_lectivo': row.id_ano_lectivo,
                'ano_activo': row.ano_activo,
                'fecha_inicio': row.fecha_inicio,
                'fecha_fin': row.fecha_fin
            })
        
        # Obtener datos para filtros
        anos_lectivos = AnoLectivo.query.order_by(AnoLectivo.ano.desc()).all()
        grados = Grado.query.order_by(Grado.nombre_grado).all()
        secciones = Seccion.query.all()
        
        # Calcular estadísticas del año actual
        total_matriculas = len(matriculas_data)
        matriculas_activas = sum(1 for m in matriculas_data if m['matricula_activa'])
        aprobados = sum(1 for m in matriculas_data if m['estado_final'] == 'Aprobado')
        reprobados = sum(1 for m in matriculas_data if m['estado_final'] == 'Reprobado')
        sin_estado = sum(1 for m in matriculas_data if not m['estado_final'] and m['matricula_activa'])
        
        return render_template("matriculas/matricula_index.html", 
                             matriculas=matriculas_data,
                             anos_lectivos=anos_lectivos,
                             grados=grados,
                             secciones=secciones,
                             ano_activo=ano_activo,
                             ano_filtro_actual=int(ano_filtro) if ano_filtro else None,
                             estadisticas={
                                 'total': total_matriculas,
                                 'activas': matriculas_activas,
                                 'aprobados': aprobados,
                                 'reprobados': reprobados,
                                 'sin_estado': sin_estado
                             })
                             
    except Exception as e:
        print(f"Error en lista_matriculas: {str(e)}")
        # Fallback básico sin JOINs
        matriculas = Matricula.query.all()
        anos_lectivos = AnoLectivo.query.all()
        grados = Grado.query.all()
        secciones = Seccion.query.all()
        ano_activo = AnoLectivo.query.filter_by(activo=True).first()
        
        return render_template("matriculas/matricula_index.html", 
                             matriculas=matriculas,
                             anos_lectivos=anos_lectivos,
                             grados=grados,
                             secciones=secciones,
                             ano_activo=ano_activo,
                             estadisticas={'total': 0, 'activas': 0, 'aprobados': 0, 'reprobados': 0, 'sin_estado': 0})

# CREAR MATRÍCULA - SIN NÚMERO DE LISTA
@matriculas_bp.route("/matricula/create", methods=['GET', 'POST'])
@matriculas_bp.route("/matricula/create/<int:id_estudiante>", methods=['GET', 'POST'])
def crear_matricula(id_estudiante=None):
    if request.method == 'POST':
        try:
            id_estudiante = request.form.get('id_estudiante')
            id_seccion = request.form.get('id_seccion')
            fecha_matricula = request.form.get('fecha_matricula')

            # Validar campos obligatorios (sin número de lista)
            if not id_estudiante or not id_seccion:
                return jsonify({
                    "success": False, 
                    "mensaje": "Todos los campos marcados con * son obligatorios."
                })

            # Obtener sección seleccionada
            seccion = Seccion.query.get(id_seccion)
            if not seccion:
                return jsonify({
                    "success": False, 
                    "mensaje": "La sección seleccionada no existe."
                })

            # Obtener estudiante
            estudiante = Estudiante.query.get(id_estudiante)
            if not estudiante:
                return jsonify({
                    "success": False, 
                    "mensaje": "El estudiante seleccionado no existe."
                })

            # Validar que el estudiante esté activo
            if not estudiante.activo:
                return jsonify({
                    "success": False, 
                    "mensaje": "El estudiante seleccionado está inactivo."
                })

            # Validar estado final del año lectivo anterior
            ano_lectivo_actual = AnoLectivo.query.get(seccion.id_ano_lectivo)
            if ano_lectivo_actual:
                # Buscar la ÚLTIMA matrícula del estudiante con estado final
                query_ano_anterior = text("""
                    SELECT 
                        pa.estado_final, 
                        al.ano, 
                        g.id_grado, 
                        g.nombre_grado, 
                        g.nivel,
                        al.id_ano_lectivo
                    FROM matriculas m
                    INNER JOIN secciones s ON m.id_seccion = s.id_seccion
                    INNER JOIN grados g ON s.id_grado = g.id_grado
                    INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
                    LEFT JOIN (
                        SELECT DISTINCT c.id_estudiante, pa.estado_final, p.id_ano_lectivo
                        FROM calificaciones c
                        INNER JOIN periodos p ON c.id_periodo = p.id_periodo
                        INNER JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
                        INNER JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
                    ) pa ON pa.id_estudiante = m.id_estudiante AND pa.id_ano_lectivo = al.id_ano_lectivo
                    WHERE m.id_estudiante = :id_estudiante
                    AND al.ano < :ano_actual
                    ORDER BY al.ano DESC, m.fecha_matricula DESC
                    LIMIT 1
                """)
                
                resultado_ano_anterior = db.session.execute(query_ano_anterior, {
                    'id_estudiante': id_estudiante,
                    'ano_actual': ano_lectivo_actual.ano
                }).fetchone()
                
                # Si tiene matrícula anterior, verificar el estado
                if resultado_ano_anterior:
                    estado = resultado_ano_anterior.estado_final
                    ano_anterior = resultado_ano_anterior.ano
                    grado_anterior_id = resultado_ano_anterior.id_grado
                    grado_anterior_nombre = f"{resultado_ano_anterior.nombre_grado} {resultado_ano_anterior.nivel}"
                    
                    # Obtener el grado de la sección seleccionada
                    grado_nuevo = Grado.query.get(seccion.id_grado)
                    
                    # Si no tiene estado final, no puede matricularse en un nuevo año
                    if not estado or estado == 'Pendiente':
                        return jsonify({
                            "success": False, 
                            "mensaje": f"El estudiante tiene matrícula en {grado_anterior_nombre} ({ano_anterior}) sin evaluación final completa. El coordinador debe asignar el estado final (Aprobado/Reprobado) antes de matricularse en un nuevo año."
                        })
                    
                    elif estado == 'Reprobado':
                        # Si reprobó, solo puede matricularse en el MISMO grado o en uno INFERIOR
                        if grado_nuevo.id_grado > grado_anterior_id:
                            return jsonify({
                                "success": False, 
                                "mensaje": f"El estudiante reprobó {grado_anterior_nombre} en el año {ano_anterior}. Solo puede matricularse nuevamente en {grado_anterior_nombre} o en un grado inferior para repetir."
                            })
                        # Si es el mismo grado o inferior, puede continuar (está repitiendo)
                        
                    elif estado == 'Aprobado':
                        # Si aprobó, NO puede matricularse en el mismo grado o inferior
                        if grado_nuevo.id_grado <= grado_anterior_id:
                            return jsonify({
                                "success": False, 
                                "mensaje": f"El estudiante ya aprobó {grado_anterior_nombre} en el año {ano_anterior}. Debe matricularse en un grado superior, no puede repetir un grado ya aprobado."
                            })
                        # Si es un grado superior, puede continuar

            # Validar que el estudiante no esté inscrito ya en ese año lectivo
            existente = (
                db.session.query(Matricula)
                .join(Seccion, Matricula.id_seccion == Seccion.id_seccion)
                .filter(
                    Matricula.id_estudiante == id_estudiante,
                    Seccion.id_ano_lectivo == seccion.id_ano_lectivo,
                    Matricula.activa == True
                )
                .first()
            )
            if existente:
                # Obtener el año lectivo para mostrar en el mensaje
                ano_lectivo = AnoLectivo.query.get(seccion.id_ano_lectivo)
                ano_text = ano_lectivo.ano if ano_lectivo else 'N/A'
                return jsonify({
                    "success": False, 
                    "mensaje": f"El estudiante ya está matriculado en una sección del año lectivo {ano_text}."
                })

            # Crear nueva matrícula (sin número de lista)
            nueva_matricula = Matricula(
                id_estudiante=id_estudiante,
                id_seccion=id_seccion,
                fecha_matricula=datetime.strptime(fecha_matricula, '%Y-%m-%d') if fecha_matricula else datetime.utcnow().date(),
                activa=True
            )
            
            db.session.add(nueva_matricula)
            db.session.commit()

            return jsonify({
                "success": True,
                "mensaje": "Matrícula creada correctamente.",
                "redirect": url_for('matricula.lista_matriculas')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False, 
                "mensaje": f"Error al crear la matrícula: {str(e)}"
            })

    # GET: Mostrar formulario
    estudiantes = Estudiante.query.filter_by(activo=True).order_by(Estudiante.nombres, Estudiante.apellidos).all()
    
    # Obtener solo las secciones del año lectivo activo
    secciones_query = text("""
        SELECT s.id_seccion, s.nombre_seccion, g.id_grado, g.nombre_grado, g.nivel, al.ano 
        FROM secciones s
        JOIN grados g ON s.id_grado = g.id_grado
        JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
        WHERE al.activo = 1
        ORDER BY g.nombre_grado, s.nombre_seccion
    """)
    
    secciones_result = db.session.execute(secciones_query)
    secciones_data = []
    for row in secciones_result:
        secciones_data.append({
            'id_seccion': row.id_seccion,
            'id_grado': row.id_grado,
            'nombre_completo': f"{row.nombre_grado} {row.nivel} - Sección {row.nombre_seccion} - Año {row.ano}",
            'nombre_seccion': row.nombre_seccion,
            'grado': row.nombre_grado,
            'nivel': row.nivel,
            'ano_lectivo': row.ano
        })
    
    return render_template("matriculas/matricula_form.html", 
                       matricula=None, 
                       estudiantes=estudiantes, 
                       secciones=secciones_data,
                       id_estudiante=id_estudiante)

# EDITAR MATRÍCULA - SIN NÚMERO DE LISTA
@matriculas_bp.route("/matricula/edit/<int:id>", methods=['GET', 'POST'])
def editar_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            id_estudiante = request.form.get('id_estudiante')
            id_seccion = request.form.get('id_seccion')
            fecha_matricula = request.form.get('fecha_matricula')

            # Validar campos obligatorios (sin número de lista)
            if not id_estudiante or not id_seccion:
                return jsonify({
                    "success": False, 
                    "mensaje": "Todos los campos marcados con * son obligatorios."
                })

            # Obtener sección seleccionada
            seccion = Seccion.query.get(id_seccion)
            if not seccion:
                return jsonify({
                    "success": False, 
                    "mensaje": "La sección seleccionada no existe."
                })

            # Obtener estudiante
            estudiante = Estudiante.query.get(id_estudiante)
            if not estudiante:
                return jsonify({
                    "success": False, 
                    "mensaje": "El estudiante seleccionado no existe."
                })

            # Validar que el estudiante esté activo
            if not estudiante.activo:
                return jsonify({
                    "success": False, 
                    "mensaje": "El estudiante seleccionado está inactivo."
                })

            # Validar estado final del año lectivo anterior (solo si cambió el año lectivo)
            matricula_actual = Matricula.query.get(id)
            seccion_actual = Seccion.query.get(matricula_actual.id_seccion)
            
            # Solo validar si está cambiando a un año lectivo diferente
            if seccion_actual.id_ano_lectivo != seccion.id_ano_lectivo:
                ano_lectivo_nuevo = AnoLectivo.query.get(seccion.id_ano_lectivo)
                if ano_lectivo_nuevo:
                    # Buscar la ÚLTIMA matrícula del estudiante (año más reciente)
                    query_ano_anterior = text("""
                        SELECT pa.estado_final, al.ano, g.id_grado, g.nombre_grado, g.nivel
                        FROM matriculas m
                        INNER JOIN secciones s ON m.id_seccion = s.id_seccion
                        INNER JOIN grados g ON s.id_grado = g.id_grado
                        INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
                        LEFT JOIN calificaciones c ON c.id_estudiante = m.id_estudiante
                        LEFT JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
                        LEFT JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
                        WHERE m.id_estudiante = :id_estudiante
                        AND (al.ano < :ano_nuevo OR (al.ano = :ano_nuevo AND al.id_ano_lectivo != :id_ano_nuevo))
                        AND m.id_matricula != :id_matricula_actual
                        AND m.activa = 1
                        ORDER BY al.ano DESC, g.id_grado DESC
                        LIMIT 1
                    """)
                    
                    resultado_ano_anterior = db.session.execute(query_ano_anterior, {
                        'id_estudiante': id_estudiante,
                        'ano_nuevo': ano_lectivo_nuevo.ano,
                        'id_ano_nuevo': seccion.id_ano_lectivo,
                        'id_matricula_actual': id
                    }).first()
                    
                    # Si tiene matrícula anterior, verificar el estado
                    if resultado_ano_anterior:
                        estado = resultado_ano_anterior.estado_final
                        ano_anterior = resultado_ano_anterior.ano
                        grado_anterior_id = resultado_ano_anterior.id_grado
                        grado_anterior_nombre = f"{resultado_ano_anterior.nombre_grado} {resultado_ano_anterior.nivel}"
                        
                        # Obtener el grado de la sección seleccionada
                        grado_nuevo = Grado.query.get(seccion.id_grado)
                        
                        # Si no tiene estado final, no puede matricularse
                        if not estado:
                            return jsonify({
                                "success": False, 
                                "mensaje": f"El estudiante tiene matrícula en {grado_anterior_nombre} ({ano_anterior}) pero no tiene evaluación final. El coordinador debe asignar el estado primero."
                            })
                        
                        if estado == 'Pendiente':
                            return jsonify({
                                "success": False, 
                                "mensaje": f"El estudiante tiene el estado 'Pendiente' del año {ano_anterior} en {grado_anterior_nombre}. El coordinador debe actualizar el estado primero."
                            })
                        elif estado == 'Reprobado':
                            # Si reprobó, solo puede matricularse en el MISMO grado
                            if grado_nuevo.id_grado != grado_anterior_id:
                                return jsonify({
                                    "success": False, 
                                    "mensaje": f"El estudiante reprobó el año {ano_anterior} en {grado_anterior_nombre}. Solo puede matricularse nuevamente en {grado_anterior_nombre}, no en un grado diferente."
                                })
                        elif estado == 'Aprobado':
                            # Si aprobó, NO puede matricularse en el mismo grado
                            if grado_nuevo.id_grado == grado_anterior_id:
                                return jsonify({
                                    "success": False, 
                                    "mensaje": f"El estudiante ya aprobó {grado_anterior_nombre} en el año {ano_anterior}. Debe matricularse en un grado superior."
                                })

            # Validar que no quede duplicado en el mismo año lectivo (excluyendo la actual)
            existente = (
                db.session.query(Matricula)
                .join(Seccion, Matricula.id_seccion == Seccion.id_seccion)
                .filter(
                    Matricula.id_estudiante == id_estudiante,
                    Seccion.id_ano_lectivo == seccion.id_ano_lectivo,
                    Matricula.id_matricula != id,
                    Matricula.activa == True
                )
                .first()
            )
            if existente:
                # Obtener el año lectivo para mostrar en el mensaje
                ano_lectivo = AnoLectivo.query.get(seccion.id_ano_lectivo)
                ano_text = ano_lectivo.ano if ano_lectivo else 'N/A'
                return jsonify({
                    "success": False, 
                    "mensaje": f"El estudiante ya tiene matrícula en otra sección del año lectivo {ano_text}."
                })

            # Actualizar matrícula (sin número de lista)
            matricula.id_estudiante = id_estudiante
            matricula.id_seccion = id_seccion
            if fecha_matricula:
                matricula.fecha_matricula = datetime.strptime(fecha_matricula, '%Y-%m-%d')

            db.session.commit()

            return jsonify({
                "success": True,
                "mensaje": "Matrícula actualizada correctamente.",
                "redirect": url_for('matricula.lista_matriculas')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False, 
                "mensaje": f"Error al actualizar la matrícula: {str(e)}"
            })

    # GET: Mostrar formulario de edición
    estudiantes = Estudiante.query.filter_by(activo=True).order_by(Estudiante.nombres, Estudiante.apellidos).all()
    
    # Obtener secciones con información de grado y año lectivo
    secciones_query = text("""
        SELECT s.id_seccion, s.nombre_seccion, g.id_grado, g.nombre_grado, g.nivel, al.ano 
        FROM secciones s
        JOIN grados g ON s.id_grado = g.id_grado
        JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
        ORDER BY al.ano DESC, g.nombre_grado, s.nombre_seccion
    """)
    
    secciones_result = db.session.execute(secciones_query)
    secciones_data = []
    for row in secciones_result:
        secciones_data.append({
            'id_seccion': row.id_seccion,
            'id_grado': row.id_grado,
            'nombre_completo': f"{row.nombre_grado} {row.nivel} - Sección {row.nombre_seccion} - Año {row.ano}",
            'nombre_seccion': row.nombre_seccion,
            'grado': row.nombre_grado,
            'nivel': row.nivel,
            'ano_lectivo': row.ano
        })
    
    return render_template("matriculas/matricula_form.html", 
                         matricula=matricula, 
                         estudiantes=estudiantes, 
                         secciones=secciones_data)

# DESACTIVAR MATRÍCULA
@matriculas_bp.route("/matricula/deactivate/<int:id>", methods=['POST'])
def desactivar_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    if not matricula.activa:
        return jsonify({"success": False, "mensaje": "La matrícula ya está inactiva."})

    matricula.activa = False
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Matrícula desactivada correctamente.",
        "redirect": url_for('matricula.lista_matriculas')
    })

# ACTIVAR MATRÍCULA
@matriculas_bp.route("/matricula/activate/<int:id>", methods=['POST'])
def activar_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    if matricula.activa:
        return jsonify({"success": False, "mensaje": "La matrícula ya está activa."})

    # Validar estado final del año lectivo anterior
    seccion = Seccion.query.get(matricula.id_seccion)
    ano_lectivo_actual = AnoLectivo.query.get(seccion.id_ano_lectivo)
    
    if ano_lectivo_actual:
        # Buscar la ÚLTIMA matrícula del estudiante
        query_ano_anterior = text("""
            SELECT pa.estado_final, al.ano, g.id_grado, g.nombre_grado, g.nivel
            FROM matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            INNER JOIN grados g ON s.id_grado = g.id_grado
            INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
            LEFT JOIN calificaciones c ON c.id_estudiante = m.id_estudiante
            LEFT JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
            LEFT JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
            WHERE m.id_estudiante = :id_estudiante
            AND (al.ano < :ano_actual OR (al.ano = :ano_actual AND al.id_ano_lectivo != :id_ano_actual))
            AND m.id_matricula != :id_matricula_actual
            AND m.activa = 1
            ORDER BY al.ano DESC, g.id_grado DESC
            LIMIT 1
        """)
        
        resultado_ano_anterior = db.session.execute(query_ano_anterior, {
            'id_estudiante': matricula.id_estudiante,
            'ano_actual': ano_lectivo_actual.ano,
            'id_ano_actual': seccion.id_ano_lectivo,
            'id_matricula_actual': matricula.id_matricula
        }).first()
        
        # Si tiene matrícula anterior, verificar el estado
        if resultado_ano_anterior:
            estado = resultado_ano_anterior.estado_final
            ano_anterior = resultado_ano_anterior.ano
            grado_anterior_id = resultado_ano_anterior.id_grado
            grado_anterior_nombre = f"{resultado_ano_anterior.nombre_grado} {resultado_ano_anterior.nivel}"
            
            # Obtener el grado de la matrícula a activar
            grado_matricula = Grado.query.get(seccion.id_grado)
            
            # Si no tiene estado final, no puede activarse
            if not estado:
                return jsonify({
                    "success": False, 
                    "mensaje": f"No se puede activar porque el estudiante tiene matrícula en {grado_anterior_nombre} ({ano_anterior}) sin evaluación final."
                })
            
            if estado == 'Pendiente':
                return jsonify({
                    "success": False, 
                    "mensaje": f"No se puede activar la matrícula porque el estado del año {ano_anterior} está 'Pendiente'. El coordinador debe actualizar el estado primero."
                })
            elif estado == 'Reprobado':
                # Si reprobó, solo puede estar matriculado en el MISMO grado
                if grado_matricula.id_grado != grado_anterior_id:
                    return jsonify({
                        "success": False, 
                        "mensaje": f"No se puede activar la matrícula porque el estudiante reprobó el año {ano_anterior} en {grado_anterior_nombre}. Solo puede matricularse en {grado_anterior_nombre}, no en un grado diferente."
                    })
            elif estado == 'Aprobado':
                # Si aprobó, NO puede estar en el mismo grado
                if grado_matricula.id_grado == grado_anterior_id:
                    return jsonify({
                        "success": False, 
                        "mensaje": f"No se puede activar la matrícula porque el estudiante ya aprobó {grado_anterior_nombre} en el año {ano_anterior}. Debe estar en un grado superior."
                    })

    # Validar que no tenga otra matrícula activa en el mismo año lectivo
    seccion = Seccion.query.get(matricula.id_seccion)
    existente = (
        db.session.query(Matricula)
        .join(Seccion, Matricula.id_seccion == Seccion.id_seccion)
        .filter(
            Matricula.id_estudiante == matricula.id_estudiante,
            Seccion.id_ano_lectivo == seccion.id_ano_lectivo,
            Matricula.id_matricula != matricula.id_matricula,
            Matricula.activa == True
        )
        .first()
    )
    if existente:
        # Obtener el año lectivo para mostrar en el mensaje
        ano_lectivo = AnoLectivo.query.get(seccion.id_ano_lectivo)
        ano_text = ano_lectivo.ano if ano_lectivo else 'N/A'
        return jsonify({"success": False, "mensaje": f"El estudiante ya tiene otra matrícula activa en el año lectivo {ano_text}."})

    matricula.activa = True
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Matrícula activada correctamente.",
        "redirect": url_for('matricula.lista_matriculas')
    })


# API PARA VERIFICAR ESTADO DEL ESTUDIANTE
@matriculas_bp.route("/api/estudiante/<int:id_estudiante>/verificar-estado", methods=['GET'])
def verificar_estado_estudiante(id_estudiante):
    """Verifica el estado final del estudiante en años lectivos anteriores"""
    try:
        ano_lectivo_nuevo = request.args.get('ano_lectivo', type=int)
        id_grado_nuevo = request.args.get('id_grado', type=int)
        
        if not ano_lectivo_nuevo:
            return jsonify({
                "success": False,
                "mensaje": "Debe seleccionar un año lectivo"
            })
        
        # Buscar la ÚLTIMA matrícula del estudiante (no solo del año anterior)
        query_estado = text("""
            SELECT 
                pa.estado_final,
                al.ano,
                g.id_grado,
                g.nombre_grado,
                g.nivel,
                s.nombre_seccion,
                # campo eliminado: conducta_final
            FROM matriculas m
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            INNER JOIN grados g ON s.id_grado = g.id_grado
            INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
            LEFT JOIN calificaciones c ON c.id_estudiante = m.id_estudiante
            LEFT JOIN promedios_periodo pp ON pp.id_calificacion = c.id_calificacion
            LEFT JOIN promedios_anuales pa ON pa.id_promedio_periodo = pp.id_promedio_periodo
            WHERE m.id_estudiante = :id_estudiante
            AND (al.ano < :ano_nuevo OR (al.ano = :ano_nuevo AND al.id_ano_lectivo != (
                SELECT id_ano_lectivo FROM anos_lectivos WHERE ano = :ano_nuevo ORDER BY id_ano_lectivo DESC LIMIT 1
            )))
            AND m.activa = 1
            ORDER BY al.ano DESC, g.id_grado DESC
            LIMIT 1
        """)
        
        resultado = db.session.execute(query_estado, {
            'id_estudiante': id_estudiante,
            'ano_nuevo': ano_lectivo_nuevo
        }).first()
        
        if resultado:
            estado = resultado.estado_final
            grado_anterior_id = resultado.id_grado
            grado_anterior_nombre = f"{resultado.nombre_grado} {resultado.nivel}"
            
            # Determinar si puede matricularse según el estado y grado
            puede_matricularse = True
            mensaje = ""
            
            # Si no tiene evaluación final
            if not estado:
                puede_matricularse = False
                mensaje = f"⚠️ El estudiante tiene matrícula en {grado_anterior_nombre} ({resultado.ano}) pero no tiene evaluación final. El coordinador debe asignar el estado (Aprobado/Reprobado) antes de continuar."
            elif estado == 'Pendiente':
                puede_matricularse = False
                mensaje = f"⏳ El estado del año {resultado.ano} en {grado_anterior_nombre} está pendiente. El coordinador debe actualizarlo primero."
            elif estado == 'Reprobado':
                # Puede matricularse SOLO en el mismo grado
                if id_grado_nuevo and id_grado_nuevo != grado_anterior_id:
                    puede_matricularse = False
                    mensaje = f"❌ El estudiante reprobó {grado_anterior_nombre} en {resultado.ano}. Solo puede repetir {grado_anterior_nombre}, no puede avanzar a otro grado."
                else:
                    puede_matricularse = True
                    mensaje = f"⚠️ El estudiante reprobó {grado_anterior_nombre} en {resultado.ano}. Puede matricularse para repetir el mismo grado."
            elif estado == 'Aprobado':
                # NO puede matricularse en el mismo grado
                if id_grado_nuevo and id_grado_nuevo == grado_anterior_id:
                    puede_matricularse = False
                    mensaje = f"❌ El estudiante ya aprobó {grado_anterior_nombre} en {resultado.ano}. Debe matricularse en un grado superior."
                else:
                    puede_matricularse = True
                    mensaje = f"✅ El estudiante aprobó {grado_anterior_nombre} en {resultado.ano}. Puede matricularse en un grado superior."
            
            return jsonify({
                "success": True,
                "tiene_registro_anterior": True,
                "ano_anterior": resultado.ano,
                "grado_anterior": grado_anterior_nombre,
                "grado_anterior_id": grado_anterior_id,
                "estado_final": estado,
                # "conducta_final" eliminado
                # "asistencia_final" eliminado
                "puede_matricularse": puede_matricularse,
                "mensaje": mensaje
            })
        else:
            return jsonify({
                "success": True,
                "tiene_registro_anterior": False,
                "puede_matricularse": True,
                "mensaje": "ℹ️ El estudiante no tiene registros en años anteriores. Puede matricularse."
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "mensaje": f"Error al verificar estado: {str(e)}"
        })


@matriculas_bp.route('/matricula/delete/<int:id>', methods=['POST'])
def eliminar_matricula(id):
    try:
        # Obtener la matrícula
        matricula = Matricula.query.get_or_404(id)
        
        # Obtener información del estudiante para el mensaje
        estudiante = Estudiante.query.get(matricula.id_estudiante)
        seccion = Seccion.query.get(matricula.id_seccion)
        grado = Grado.query.get(seccion.id_grado)
        ano_lectivo = AnoLectivo.query.get(seccion.id_ano_lectivo)
        
        estudiante_nombre = f"{estudiante.nombres} {estudiante.apellidos}"
        seccion_info = f"{grado.nombre_grado} {grado.nivel} Sección {seccion.nombre_seccion} ({ano_lectivo.ano})"
        
        # Verificar si el estudiante tiene calificaciones asociadas a esta matrícula
        query_calificaciones = text("""
            SELECT COUNT(*) 
            FROM calificaciones c
            INNER JOIN matriculas m ON c.id_estudiante = m.id_estudiante
            INNER JOIN periodos p ON c.id_periodo = p.id_periodo
            INNER JOIN secciones s ON m.id_seccion = s.id_seccion
            WHERE m.id_matricula = :id_matricula
            AND p.id_ano_lectivo = s.id_ano_lectivo
        """)
        
        total_calificaciones = db.session.execute(
            query_calificaciones,
            {'id_matricula': id}
        ).scalar()
        
        if total_calificaciones > 0:
            return jsonify({
                "success": False,
                "icon": "warning",
                "mensaje": f"⚠️ No se puede eliminar la matrícula de <strong>{estudiante_nombre}</strong> en {seccion_info}.<br><br>"
                          f"El estudiante tiene <strong>{total_calificaciones} calificación(es)</strong> registrada(s) en este año lectivo.<br><br>"
                          f"<span style='color: #dc2626;'>Para eliminar esta matrícula, primero debe eliminar todas las calificaciones del estudiante.</span>"
            })
        
        # Si no hay calificaciones, proceder con la eliminación
        db.session.delete(matricula)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "icon": "success",
            "mensaje": f"✅ Matrícula de <strong>{estudiante_nombre}</strong> en {seccion_info} eliminada exitosamente.",
            "redirect": url_for('matricula.lista_matriculas')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "icon": "error",
            "mensaje": f"❌ Error al eliminar la matrícula: {str(e)}"
        })
