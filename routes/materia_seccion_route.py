from flask import Blueprint, render_template, request, jsonify, url_for
from models.MateriaSeccion import MateriaSeccion
from models.Materias import Materia
from models.Secciones import Seccion
from models.usuarios import Usuario
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo
from db import db
from sqlalchemy import text

# Blueprint para asignación de materias
materia_seccion_bp = Blueprint('materia_seccion', __name__, template_folder="templates")

# LISTAR ASIGNACIONES - SIN PERÍODO
@materia_seccion_bp.route("/")
def lista_asignaciones():
    try:
        # Consulta SQL para obtener todas las asignaciones con información relacionada (sin período)
        query = text("""
            SELECT 
                ms.id_asignacion,
                m.nombre_materia,
                m.codigo_materia,
                g.nombre_grado,
                g.nivel,
                s.nombre_seccion,
                al.ano as ano_lectivo,
                u.nombres as maestro_nombres,
                u.apellidos as maestro_apellidos,
                u.usuario as maestro_usuario
            FROM materia_seccion ms
            JOIN materias m ON ms.id_materia = m.id_materia
            JOIN secciones s ON ms.id_seccion = s.id_seccion
            JOIN grados g ON s.id_grado = g.id_grado
            JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
            JOIN usuarios u ON ms.id_maestro = u.id_usuario
            ORDER BY al.ano DESC, g.nombre_grado, s.nombre_seccion, m.nombre_materia
        """)
        
        result = db.session.execute(query)
        asignaciones_data = []
        
        for row in result:
            asignaciones_data.append({
                'id_asignacion': row.id_asignacion,
                'nombre_materia': row.nombre_materia,
                'codigo_materia': row.codigo_materia,
                'nombre_grado': row.nombre_grado,
                'nivel': row.nivel,
                'nombre_seccion': row.nombre_seccion,
                'ano_lectivo': row.ano_lectivo,
                'maestro_nombres': row.maestro_nombres,
                'maestro_apellidos': row.maestro_apellidos,
                'maestro_usuario': row.maestro_usuario
            })
        
        # Obtener datos para filtros (sin períodos)
        anos_lectivos = AnoLectivo.query.order_by(AnoLectivo.ano.desc()).all()
        grados = Grado.query.order_by(Grado.nombre_grado).all()
        materias = Materia.query.filter_by(activa=True).order_by(Materia.nombre_materia).all()
        
        return render_template("materia_seccion/asignacion_index.html", 
                             asignaciones=asignaciones_data,
                             anos_lectivos=anos_lectivos,
                             grados=grados,
                             materias=materias)
                             
    except Exception as e:
        print(f"Error en lista_asignaciones: {str(e)}")
        asignaciones = MateriaSeccion.query.all()
        return render_template("materia_seccion/asignacion_index.html", 
                             asignaciones=asignaciones,
                             anos_lectivos=[],
                             grados=[],
                             materias=[])

# CREAR ASIGNACIÓN - SIN PERÍODO
@materia_seccion_bp.route("/asignacion/create", methods=['GET', 'POST'])
def crear_asignacion():
    if request.method == 'POST':
        try:
            id_materia = request.form.get('id_materia')
            id_seccion = request.form.get('id_seccion')
            id_maestro = request.form.get('id_maestro')

            # Validar campos obligatorios (sin período)
            if not all([id_materia, id_seccion, id_maestro]):
                return jsonify({
                    "success": False, 
                    "mensaje": "Todos los campos son obligatorios."
                })

            # Validar que la materia esté activa
            materia = Materia.query.get(id_materia)
            if not materia or not materia.activa:
                return jsonify({
                    "success": False, 
                    "mensaje": "La materia seleccionada no está disponible."
                })

            # Validar que el maestro sea docente y esté activo
            maestro = Usuario.query.get(id_maestro)
            if not maestro or not maestro.activo or maestro.id_rol != 2:  # 2 = Docente
                return jsonify({
                    "success": False, 
                    "mensaje": "El usuario seleccionado no es un docente activo."
                })

            # Validar que no exista asignación duplicada (sin período)
            existente = MateriaSeccion.query.filter_by(
                id_materia=id_materia,
                id_seccion=id_seccion
            ).first()

            if existente:
                return jsonify({
                    "success": False, 
                    "mensaje": "Ya existe una asignación para esta materia y sección."
                })

            # Crear nueva asignación (sin período)
            nueva_asignacion = MateriaSeccion(
                id_materia=id_materia,
                id_seccion=id_seccion,
                id_maestro=id_maestro
            )
            
            db.session.add(nueva_asignacion)
            db.session.commit()

            return jsonify({
                "success": True,
                "mensaje": "Asignación creada correctamente.",
                "redirect": url_for('materia_seccion.lista_asignaciones')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False, 
                "mensaje": f"Error al crear la asignación: {str(e)}"
            })

    # GET: Mostrar formulario (sin períodos)
    materias = Materia.query.filter_by(activa=True).order_by(Materia.nombre_materia).all()
    
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
    
    docentes = Usuario.query.filter_by(id_rol=2, activo=True).order_by(Usuario.nombres, Usuario.apellidos).all()
    
    return render_template("materia_seccion/asignacion_form.html", 
                         asignacion=None, 
                         materias=materias,
                         secciones=secciones_data,
                         docentes=docentes)

# EDITAR ASIGNACIÓN - SIN PERÍODO
@materia_seccion_bp.route("/asignacion/edit/<int:id>", methods=['GET', 'POST'])
def editar_asignacion(id):
    asignacion = MateriaSeccion.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            id_materia = request.form.get('id_materia')
            id_seccion = request.form.get('id_seccion')
            id_maestro = request.form.get('id_maestro')

            # Validar campos obligatorios (sin período)
            if not all([id_materia, id_seccion, id_maestro]):
                return jsonify({
                    "success": False, 
                    "mensaje": "Todos los campos son obligatorios."
                })

            # Validar que la materia esté activa
            materia = Materia.query.get(id_materia)
            if not materia or not materia.activa:
                return jsonify({
                    "success": False, 
                    "mensaje": "La materia seleccionada no está disponible."
                })

            # Validar que el maestro sea docente y esté activo
            maestro = Usuario.query.get(id_maestro)
            if not maestro or not maestro.activo or maestro.id_rol != 2:
                return jsonify({
                    "success": False, 
                    "mensaje": "El usuario seleccionado no es un docente activo."
                })

            # Validar que no exista asignación duplicada (excluyendo la actual, sin período)
            existente = MateriaSeccion.query.filter(
                MateriaSeccion.id_materia == id_materia,
                MateriaSeccion.id_seccion == id_seccion,
                MateriaSeccion.id_asignacion != id
            ).first()

            if existente:
                return jsonify({
                    "success": False, 
                    "mensaje": "Ya existe una asignación para esta materia y sección."
                })

            # Actualizar asignación (sin período)
            asignacion.id_materia = id_materia
            asignacion.id_seccion = id_seccion
            asignacion.id_maestro = id_maestro

            db.session.commit()

            return jsonify({
                "success": True,
                "mensaje": "Asignación actualizada correctamente.",
                "redirect": url_for('materia_seccion.lista_asignaciones')
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False, 
                "mensaje": f"Error al actualizar la asignación: {str(e)}"
            })

    # GET: Mostrar formulario de edición (sin períodos)
    materias = Materia.query.filter_by(activa=True).order_by(Materia.nombre_materia).all()
    
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
    
    docentes = Usuario.query.filter_by(id_rol=2, activo=True).order_by(Usuario.nombres, Usuario.apellidos).all()
    
    return render_template("materia_seccion/asignacion_form.html", 
                         asignacion=asignacion, 
                         materias=materias,
                         secciones=secciones_data,
                         docentes=docentes)

# ELIMINAR ASIGNACIÓN - SIN CAMBIOS
@materia_seccion_bp.route("/asignacion/delete/<int:id>", methods=['POST'])
def eliminar_asignacion(id):
    asignacion = MateriaSeccion.query.get_or_404(id)
    
    try:
        db.session.delete(asignacion)
        db.session.commit()

        return jsonify({
            "success": True,
            "mensaje": "Asignación eliminada correctamente.",
            "redirect": url_for('materia_seccion.lista_asignaciones')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False, 
            "mensaje": f"Error al eliminar la asignación: {str(e)}"
        })