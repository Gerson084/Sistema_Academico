from flask import Blueprint, render_template, request, redirect, url_for
from models.Estudiantes import Estudiante
from db import db
from datetime import datetime

# Crear Blueprint
estudiantes_bp = Blueprint('estudiantes', __name__, template_folder="templates")

# Listar estudiantes (vista HTML)
@estudiantes_bp.route('/')
def lista_estudiantes():
    estudiantes = Estudiante.query.all()
    return render_template("estudiantes/lista.html", estudiantes=estudiantes)

# Crear estudiante (formulario y guardado)
@estudiantes_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_estudiante():
    if request.method == 'POST':
        nuevo = Estudiante(
            nie=request.form.get('nie'),
            nombres=request.form.get('nombres'),
            apellidos=request.form.get('apellidos'),
            fecha_nacimiento=request.form.get('fecha_nacimiento'),
            genero=request.form.get('genero'),
            direccion=request.form.get('direccion'),
            telefono=request.form.get('telefono'),
            email=request.form.get('email'),
            nombre_padre=request.form.get('nombre_padre'),
            nombre_madre=request.form.get('nombre_madre'),
            telefono_emergencia=request.form.get('telefono_emergencia'),
            fecha_ingreso=request.form.get('fecha_ingreso'),
            activo=request.form.get('activo', '1') == '1',
            fecha_creacion=datetime.utcnow()
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('estudiantes.lista_estudiantes'))
    return render_template("estudiantes/nuevo.html")

# Editar estudiante
@estudiantes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        estudiante.nie = request.form.get('nie')
        estudiante.nombres = request.form.get('nombres')
        estudiante.apellidos = request.form.get('apellidos')
        estudiante.fecha_nacimiento = request.form.get('fecha_nacimiento')
        estudiante.genero = request.form.get('genero')
        estudiante.direccion = request.form.get('direccion')
        estudiante.telefono = request.form.get('telefono')
        estudiante.email = request.form.get('email')
        estudiante.nombre_padre = request.form.get('nombre_padre')
        estudiante.nombre_madre = request.form.get('nombre_madre')
        estudiante.telefono_emergencia = request.form.get('telefono_emergencia')
        estudiante.fecha_ingreso = request.form.get('fecha_ingreso')
        estudiante.activo = request.form.get('activo') == '1'
        estudiante.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('estudiantes.lista_estudiantes'))
    return render_template("estudiantes/editar.html", estudiante=estudiante)

# Eliminar estudiante
@estudiantes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_estudiante(id):
    estudiante = Estudiante.query.get_or_404(id)
    db.session.delete(estudiante)
    db.session.commit()
    return redirect(url_for('estudiantes.lista_estudiantes'))
