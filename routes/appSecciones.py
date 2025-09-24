from flask import Blueprint, render_template, request, redirect, url_for
from models.Secciones import Seccion
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo

from db import db
from datetime import datetime

# Crear Blueprint
secciones_bp = Blueprint('secciones', __name__, template_folder="templates")

# Listar secciones (vista HTML)
@secciones_bp.route('/')
def lista_secciones():
    secciones = Seccion.query.all()
    return render_template("secciones/lista.html", secciones=secciones)

@secciones_bp.route('/nuevo', methods=['GET', 'POST'])
def nueva_seccion():
    if request.method == 'POST':
        nueva = Seccion(
            id_grado=request.form.get('id_grado'),
            nombre_seccion=request.form.get('nombre_seccion'),
            id_ano_lectivo=request.form.get('id_ano_lectivo')
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('secciones.lista_secciones', 
                                  success='true', 
                                  action='created'))

    grados = Grado.query.all()
    anos_lectivos = AnoLectivo.query.filter_by(activo=1).all()  # solo años activos
    return render_template("secciones/nuevo.html", grados=grados, anos_lectivos=anos_lectivos)

@secciones_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    grados = Grado.query.all()  # Traer todos los grados
    anos_lectivos = AnoLectivo.query.all()  # Traer todos los años lectivos

    if request.method == 'POST':
        seccion.id_grado = request.form.get('id_grado')
        seccion.nombre_seccion = request.form.get('nombre_seccion')
        seccion.id_ano_lectivo = request.form.get('id_ano_lectivo')
        db.session.commit()
        return redirect(url_for('secciones.lista_secciones', 
                                  success='true', 
                                  action='updated'))

    # Pasar las listas al template
    return render_template(
        "secciones/editar.html",
        seccion=seccion,
        grados=grados,
        anos_lectivos=anos_lectivos
    )


# Eliminar sección
@secciones_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    db.session.delete(seccion)
    db.session.commit()
    return redirect(url_for('secciones.lista_secciones'))
