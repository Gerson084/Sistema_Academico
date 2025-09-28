from flask import Blueprint, render_template, request, jsonify, url_for
from models.Estudiantes import Estudiante
from models.Secciones import Seccion
from models.matriculas import Matricula
from models.Grados import Grado  # Asegúrate de importar Grado
from models.AnosLectivos import AnoLectivo  # Asegúrate de importar AnoLectivo
from sqlalchemy import text  # Importar text para consultas SQL


from db import db
from datetime import datetime

# Blueprint para matrículas
matriculas_bp = Blueprint('matricula', __name__, template_folder="templates")

# LISTAR - VERSIÓN SIN MODIFICAR MODELOS
@matriculas_bp.route("/")
def lista_matriculas():
    try:
        # Consulta SQL directa con JOINs explícitos
        query = text("""
            SELECT 
                m.*,
                e.nombres as estudiante_nombres,
                e.apellidos as estudiante_apellidos,
                e.nie as estudiante_nie,
                s.nombre_seccion,
                g.nombre_grado,
                g.nivel as grado_nivel,
                al.ano as ano_lectivo,
                al.fecha_inicio,
                al.fecha_fin
            FROM matriculas m
            JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
            JOIN secciones s ON m.id_seccion = s.id_seccion
            JOIN grados g ON s.id_grado = g.id_grado
            JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
            ORDER BY m.id_matricula DESC
        """)
        
        result = db.session.execute(query)
        
        # Convertir resultado a lista de diccionarios
        matriculas_data = []
        for row in result:
            matriculas_data.append({
                'id_matricula': row.id_matricula,
                'id_estudiante': row.id_estudiante,
                'id_seccion': row.id_seccion,
                'numero_lista': row.numero_lista,
                'fecha_matricula': row.fecha_matricula,
                'activa': row.activa,
                'estudiante_nombres': row.estudiante_nombres,
                'estudiante_apellidos': row.estudiante_apellidos,
                'estudiante_nie': row.estudiante_nie,
                'nombre_seccion': row.nombre_seccion,
                'nombre_grado': row.nombre_grado,
                'grado_nivel': row.grado_nivel,
                'ano_lectivo': row.ano_lectivo,
                'fecha_inicio': row.fecha_inicio,
                'fecha_fin': row.fecha_fin
            })
        
        # Obtener datos para filtros (consultas simples)
        anos_lectivos = AnoLectivo.query.order_by(AnoLectivo.ano.desc()).all()
        grados = Grado.query.order_by(Grado.nombre_grado).all()
        secciones = Seccion.query.all()
        
        return render_template("matriculas/matricula_index.html", 
                             matriculas=matriculas_data,  # Enviar los datos procesados
                             anos_lectivos=anos_lectivos,
                             grados=grados,
                             secciones=secciones)
                             
    except Exception as e:
        print(f"Error en lista_matriculas: {str(e)}")
        # Fallback básico sin JOINs
        matriculas = Matricula.query.all()
        anos_lectivos = AnoLectivo.query.all()
        grados = Grado.query.all()
        secciones = Seccion.query.all()
        
        return render_template("matriculas/matricula_index.html", 
                             matriculas=matriculas,
                             anos_lectivos=anos_lectivos,
                             grados=grados,
                             secciones=secciones)

# CREAR MATRÍCULA - ACTUALIZADO
@matriculas_bp.route("/matricula/create", methods=['GET', 'POST'])
@matriculas_bp.route("/matricula/create/<int:id_estudiante>", methods=['GET', 'POST'])
def crear_matricula(id_estudiante=None):
    if request.method == 'POST':
        try:
            id_estudiante = request.form.get('id_estudiante')
            id_seccion = request.form.get('id_seccion')
            numero_lista = request.form.get('numero_lista')
            fecha_matricula = request.form.get('fecha_matricula')

            # Validar campos obligatorios
            if not id_estudiante or not id_seccion or not numero_lista:
                return jsonify({
                    "success": False, 
                    "mensaje": "Todos los campos marcados con * son obligatorios."
                })

            # Validar que el número de lista sea un número válido
            try:
                numero_lista = int(numero_lista)
                if numero_lista <= 0:
                    return jsonify({
                        "success": False, 
                        "mensaje": "El número de lista debe ser mayor a 0."
                    })
            except ValueError:
                return jsonify({
                    "success": False, 
                    "mensaje": "El número de lista debe ser un número válido."
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
                return jsonify({
                    "success": False, 
                    "mensaje": f"El estudiante ya está matriculado en una sección del año lectivo {seccion.id_ano_lectivo}."
                })

            # Validar que el número de lista no esté ocupado en la misma sección
            numero_existente = (
                Matricula.query
                .filter_by(id_seccion=id_seccion, numero_lista=numero_lista, activa=True)
                .first()
            )
            if numero_existente:
                return jsonify({
                    "success": False, 
                    "mensaje": f"El número de lista {numero_lista} ya está ocupado en esta sección."
                })

            # Crear nueva matrícula
            nueva_matricula = Matricula(
                id_estudiante=id_estudiante,
                id_seccion=id_seccion,
                numero_lista=numero_lista,
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
    
    # Obtener secciones con información de grado y año lectivo usando consulta SQL
    secciones_query = text("""
        SELECT s.id_seccion, s.nombre_seccion, g.nombre_grado, g.nivel, al.ano 
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

# EDITAR MATRÍCULA - ACTUALIZADO
@matriculas_bp.route("/matricula/edit/<int:id>", methods=['GET', 'POST'])
def editar_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            id_estudiante = request.form.get('id_estudiante')
            id_seccion = request.form.get('id_seccion')
            numero_lista = request.form.get('numero_lista')
            fecha_matricula = request.form.get('fecha_matricula')

            # Validar campos obligatorios
            if not id_estudiante or not id_seccion or not numero_lista:
                return jsonify({
                    "success": False, 
                    "mensaje": "Todos los campos marcados con * son obligatorios."
                })

            # Validar que el número de lista sea un número válido
            try:
                numero_lista = int(numero_lista)
                if numero_lista <= 0:
                    return jsonify({
                        "success": False, 
                        "mensaje": "El número de lista debe ser mayor a 0."
                    })
            except ValueError:
                return jsonify({
                    "success": False, 
                    "mensaje": "El número de lista debe ser un número válido."
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
                return jsonify({
                    "success": False, 
                    "mensaje": f"El estudiante ya tiene matrícula en otra sección del año lectivo {seccion.id_ano_lectivo}."
                })

            # Validar que el número de lista no esté ocupado en la misma sección (excluyendo la actual)
            numero_existente = (
                Matricula.query
                .filter(
                    Matricula.id_seccion == id_seccion,
                    Matricula.numero_lista == numero_lista,
                    Matricula.activa == True,
                    Matricula.id_matricula != id
                )
                .first()
            )
            if numero_existente:
                return jsonify({
                    "success": False, 
                    "mensaje": f"El número de lista {numero_lista} ya está ocupado en esta sección."
                })

            # Actualizar matrícula
            matricula.id_estudiante = id_estudiante
            matricula.id_seccion = id_seccion
            matricula.numero_lista = numero_lista
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
        SELECT s.id_seccion, s.nombre_seccion, g.nombre_grado, g.nivel, al.ano 
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
# DESACTIVAR
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

# ACTIVAR
@matriculas_bp.route("/matricula/activate/<int:id>", methods=['POST'])
def activar_matricula(id):
    matricula = Matricula.query.get_or_404(id)
    if matricula.activa:
        return jsonify({"success": False, "mensaje": "La matrícula ya está activa."})

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
        return jsonify({"success": False, "mensaje": "El estudiante ya tiene otra matrícula activa en este año lectivo."})

    matricula.activa = True
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Matrícula activada correctamente.",
        "redirect": url_for('matricula.lista_matriculas')
    })
