from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.Materias import Materia
from models.Grados import Grado
from models.usuarios import Usuario  # Para los docentes
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
@materias_bp.route("/materias/nueva", methods=["GET", "POST"])
def nueva_materia():
    grados = Grado.query.all()
    if request.method == "POST":
        nombre = request.form["nombre_materia"].strip()
        codigo = request.form["codigo_materia"].strip()
        id_grado = request.form["id_grado"]
        descripcion = request.form["descripcion"].strip()

        # Validaciones en backend
        if not nombre or not codigo or not id_grado:
            flash("⚠️ Todos los campos obligatorios deben estar completos.", "warning")
            return redirect(url_for("materias.nueva_materia"))

        if Materia.query.filter_by(codigo_materia=codigo).first():
            flash("❌ El código de materia ya existe, ingrese uno diferente.", "danger")
            return redirect(url_for("materias.nueva_materia"))

        try:
            materia = Materia(
                nombre_materia=nombre,
                codigo_materia=codigo,
                id_grado=id_grado,
                descripcion=descripcion,
                activa=True
            )
            db.session.add(materia)
            db.session.commit()
            flash("✅ Materia creada correctamente.", "success")
            return redirect(url_for("materias.lista_materias"))
        except Exception:
            db.session.rollback()
            flash("❌ Ocurrió un error al guardar la materia.", "danger")
            return redirect(url_for("materias.nueva_materia"))

    return render_template("materias/nuevo.html", grados=grados)

# Editar materia
@materias_bp.route("/materias/editar/<int:id>", methods=["GET", "POST"])
def editar_materia(id):
    materia = Materia.query.get_or_404(id)
    grados = Grado.query.all()

    if request.method == "POST":
        nombre = request.form["nombre_materia"].strip()
        codigo = request.form["codigo_materia"].strip()
        id_grado = request.form["id_grado"]
        descripcion = request.form["descripcion"].strip()

        # Validaciones
        if not nombre or not codigo or not id_grado:
            flash("⚠️ Todos los campos obligatorios deben estar completos.", "warning")
            return redirect(url_for("materias.editar_materia", id=id))

        # Verificar que el código no esté duplicado con otra materia
        existente = Materia.query.filter_by(codigo_materia=codigo).first()
        if existente and existente.id_materia != materia.id_materia:
            flash("❌ El código de materia ya está en uso por otra materia.", "danger")
            return redirect(url_for("materias.editar_materia", id=id))

        try:
            materia.nombre_materia = nombre
            materia.codigo_materia = codigo
            materia.id_grado = id_grado
            materia.descripcion = descripcion
            db.session.commit()
            flash("✅ Materia actualizada correctamente.", "success")
            return redirect(url_for("materias.lista_materias"))
        except Exception:
            db.session.rollback()
            flash("❌ Ocurrió un error al actualizar la materia.", "danger")
            return redirect(url_for("materias.editar_materia", id=id))

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
