from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
    return render_template("secciones/listar.html", secciones=secciones)

@secciones_bp.route('/nuevo', methods=['GET', 'POST'])
def nueva_seccion():
    if request.method == 'POST':
        nueva = Seccion(
            id_grado=request.form.get('id_grado'),
            nombre_seccion=request.form.get('nombre_seccion'),
            id_ano_lectivo=request.form.get('id_ano_lectivo'),
            activo=1
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('secciones.lista_secciones', 
                                  success='true', 
                                  action='created'))

    grados = Grado.query.all()
    anos_lectivos = AnoLectivo.query.filter_by(activo=1).all()
    return render_template("secciones/nuevo.html", grados=grados, anos_lectivos=anos_lectivos)

@secciones_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    grados = Grado.query.all()
    anos_lectivos = AnoLectivo.query.all()

    if request.method == 'POST':
        seccion.id_grado = request.form.get('id_grado')
        seccion.nombre_seccion = request.form.get('nombre_seccion')
        seccion.id_ano_lectivo = request.form.get('id_ano_lectivo')
        db.session.commit()
        return redirect(url_for('secciones.lista_secciones', 
                                  success='true', 
                                  action='updated'))

    return render_template(
        "secciones/editar.html",
        seccion=seccion,
        grados=grados,
        anos_lectivos=anos_lectivos
    )

@secciones_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    db.session.delete(seccion)
    db.session.commit()
    return redirect(url_for('secciones.lista_secciones', 
                              success='true', 
                              action='deleted'))

# Habilitar sección
@secciones_bp.route('/habilitar/<int:id>', methods=['POST'])
def habilitar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    seccion.activo = 1
    db.session.commit()
    return redirect(url_for('secciones.lista_secciones', 
                              success='true', 
                              action='enabled'))

# Deshabilitar sección

# Deshabilitar sección solo admin y si no tiene alumnos inscritos
@secciones_bp.route('/deshabilitar/<int:id>', methods=['POST'])
def deshabilitar_seccion(id):
    if not session.get('user_id') or session.get('user_role') != 1:
        flash('Acceso restringido solo para administradores.', 'danger')
        return redirect(url_for('auth.login'))
    seccion = Seccion.query.get_or_404(id)
    from models.matriculas import Matricula
    inscritos = Matricula.query.filter_by(id_seccion=id).count()
    if inscritos > 0:
        flash('No se puede deshabilitar la sección porque tiene alumnos inscritos.', 'danger')
        return redirect(url_for('secciones.lista_secciones'))
    seccion.activo = 0
    db.session.commit()
    flash('Sección deshabilitada correctamente.', 'success')
    return redirect(url_for('secciones.lista_secciones'))
