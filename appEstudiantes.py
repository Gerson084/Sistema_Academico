from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models.Estudiantes import Estudiante
from models.Secciones import Seccion
from models.matriculas import Matricula
from models.Grados import Grado
from db import db
from sqlalchemy import or_
from datetime import datetime

# Crear Blueprint
estudiantes_bp = Blueprint('estudiantes', __name__, template_folder="templates")

# Listar estudiantes (vista HTML)
@estudiantes_bp.route('/')
def lista_estudiantes():
    estudiantes = Estudiante.query.all()
    secciones = Seccion.query.all()
    grados = Grado.query.all()
    return render_template(
        "estudiantes/lista.html",
        estudiantes=estudiantes,
        secciones=secciones,
        grados=grados,
        seccion_seleccionada=None,
        grado_seleccionado=None,
        estado_seleccionado=None,
        search_term="",
    )

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



# 

@estudiantes_bp.route('/busqueda', methods=['GET'])
def filtro_estudiantes():
    seccion_id = request.args.get('Seccion_id', type=int)
    grado_id = request.args.get('Grado_id', type=int)
    estado = request.args.get('estado', default=None, type=str)
    search_term = request.args.get('search', default="", type=str)
    secciones = Seccion.query.all()
    grados = Grado.query.all()
    query = Estudiante.query

    if seccion_id or grado_id:
        query = query.join(Matricula, Matricula.id_estudiante == Estudiante.id_estudiante)
        if grado_id:
            query = query.join(Seccion, Seccion.id_seccion == Matricula.id_seccion).filter(Seccion.id_grado == grado_id)
        if seccion_id:
            query = query.filter(Matricula.id_seccion == seccion_id)
    # Filtro por estado (activos / inactivos)
    if estado == 'activos':
        query = query.filter(Estudiante.activo == True)
    elif estado == 'inactivos':
        query = query.filter(Estudiante.activo == False)
    # Optional text search
    if search_term:
        like = f"%{search_term}%"
        query = query.filter(
            or_(
                Estudiante.nombres.ilike(like),
                Estudiante.apellidos.ilike(like),
                Estudiante.nie.ilike(like),
                Estudiante.email.ilike(like),
            )
        )
    estudiantes = query.distinct().all()
    return render_template(
        "estudiantes/lista.html",
        estudiantes=estudiantes,
        secciones=secciones,
        grados=grados,
        seccion_seleccionada=seccion_id,
        grado_seleccionado=grado_id,
        estado_seleccionado=estado,
        search_term=search_term,
    )



    


