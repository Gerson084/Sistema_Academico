from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.Materias import Materia
from models.Grados import Grado
from models.usuarios import Usuario 
from models.MateriaSeccion import MateriaSeccion

from db import db

materias_bp = Blueprint('materias', __name__, template_folder="templates")

# Listar materias
@materias_bp.route('/')
def lista_materias():
    materias = Materia.query.all()
    success = request.args.get('success')
    action = request.args.get('action')
    return render_template("materias/listar.html", materias=materias, success=success, action=action)

# Nueva materia
@materias_bp.route("/create", methods=["GET", "POST"])
def nueva_materia():
    grados = Grado.query.all()
    if request.method == "POST":
        nombre = request.form["nombre_materia"].strip()
        codigo = request.form["codigo_materia"].strip()
        descripcion = request.form["descripcion"].strip()


        # Validaciones en backend
        if not nombre or not codigo :
            return jsonify({
                "success": False,
                "mensaje": "⚠️ Todos los campos obligatorios deben estar completos."
            })

        if Materia.query.filter_by(codigo_materia=codigo).first():
            return jsonify({
                "success": False,
                "mensaje": "❌ El código de materia ya existe, ingrese uno diferente."
            })

        try:
            materia = Materia(
                
                nombre_materia=nombre,
                codigo_materia=codigo,
                descripcion=descripcion,
                activa=True
            )

            db.session.add(materia)
            db.session.commit()
            return jsonify({
            "success": True,
            "mensaje": "Materia creada correctamente.",
            "redirect": url_for('materias.lista_materias')
        })
            
        except Exception as e:
            db.session.rollback()
            print("Error al guardar materia:", e)
            return jsonify({
                "success": False,
                "mensaje": "❌ Ocurrió un error al guardar la materia.",
                "redirect": url_for('materias.lista_materias')

            })


    return render_template("materias/nuevo.html", grados=grados)


# Editar materia solo admin
@materias_bp.route("/materias/editar/<int:id>", methods=["GET", "POST"])
def editar_materia(id):
    if not session.get('user_id') or session.get('user_role') != 1:
        flash('Acceso restringido solo para administradores.', 'danger')
        return redirect(url_for('auth.login'))
    materia = Materia.query.get_or_404(id)
    grados = Grado.query.all()

    if request.method == "POST":
        nombre = request.form["nombre_materia"].strip()
        codigo = request.form["codigo_materia"].strip()
        descripcion = request.form["descripcion"].strip()

        # Validaciones
        if not nombre or not codigo :
            return jsonify({
                "success": False,
                "icon": "warning",
                "mensaje": "Todos los campos son obligatorios.",
                "redirect": url_for("materias.editar_materia", id=id)

            })

        # Verificar que el código no esté duplicado con otra materia
        existente = Materia.query.filter_by(codigo_materia=codigo).first()
        if existente and existente.id_materia != materia.id_materia:
            return jsonify({
                "success": False,
                "mensaje": "El codigo de materia ya existe.",
                "icon": "warning",
                "redirect": url_for("materias.editar_materia", id=id)

            })
            

        try:
            materia.nombre_materia = nombre
            materia.codigo_materia = codigo
            materia.descripcion = descripcion
            db.session.commit()
            return jsonify({
                "success": True,
                "icon": "success",
                "mensaje": " Materia Actualizada Correctamente.",
                "redirect": url_for('materias.lista_materias')

            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False,
                "mensaje": "❌ Ocurrió un error al guardar la materia.",
                "redirect": url_for('materias.lista_materias')

            })

    return render_template("materias/editar.html", materia=materia, grados=grados)

# Eliminar materia
@materias_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_materia(id):
    materia = Materia.query.get_or_404(id)
    db.session.delete(materia)
    db.session.commit()
    return redirect(url_for('materias.lista_materias', success='true', action='deleted'))

# Deshabilitar materia
@materias_bp.route('/deshabilitar/<int:id>', methods=['POST'])
def deshabilitar_materia(id):
    # asignacion = Grado.query.join(MateriaSeccion).select_from(MateriaSeccion.id_materia == id).first()

    asignacion = MateriaSeccion.query.filter_by(id_materia=id).first()
    if asignacion:
        return jsonify({
                "success": False,
                "title": "Error al desactivar",
                "mensaje": "Materia asignada a un grado.",
                "redirect": url_for('materias.lista_materias')

            })
        return redirect(url_for('materias.lista_materias', success='false'))

    materia = Materia.query.get_or_404(id)
    materia.activa = False
    db.session.commit()
    return redirect(url_for('materias.lista_materias', success='true', action='disabled'))

# Habilitar materia
@materias_bp.route('/habilitar/<int:id>', methods=['POST'])
def habilitar_materia(id):
    materia = Materia.query.get_or_404(id)
    materia.activa = True
    db.session.commit()
    return redirect(url_for('materias.lista_materias', success='true', action='enabled'))


# Asignar materia a docente
@materias_bp.route('/asignar/<int:id>', methods=['GET', 'POST'])
def asignar_docente(id):
    materia = Materia.query.get_or_404(id)
    docentes = Usuario.query.filter_by(rol='docente', activo=True).all()
    if request.method == 'POST':
        docente_id = request.form.get('docente_id')
        if docente_id:
            materia.docente_id = docente_id
            db.session.commit()
            return redirect(url_for('materias.lista_materias', success='true', action='assigned'))
    return render_template("materias/asignar.html", materia=materia, docentes=docentes)
