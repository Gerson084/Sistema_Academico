from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.Secciones import Seccion
from models.Grados import Grado
from models.usuarios import Usuario
from models.AnosLectivos import AnoLectivo
from db import db
from datetime import datetime

# Crear Blueprint
secciones_bp = Blueprint('secciones', __name__, template_folder="templates")

# Listar secciones (vista HTML)


@secciones_bp.route('/')
def lista_secciones():
    # Usar joinedload para cargar las relaciones de una vez (más eficiente)
    from sqlalchemy.orm import joinedload
    
    secciones = Seccion.query.options(
        joinedload(Seccion.coordinador),
        joinedload(Seccion.grado),
        joinedload(Seccion.ano_lectivo)
    ).all()
    
    return render_template("secciones/listar.html", secciones=secciones)

@secciones_bp.route('/nuevo', methods=['GET', 'POST'])
def nueva_seccion():
    if request.method == 'POST':
        id_grado = request.form.get('id_grado')
        id_coordinador = request.form.get('id_coordinador')  # Corregido
        nombre_seccion = request.form.get('nombre_seccion').strip().upper()
        id_ano_lectivo = request.form.get('id_ano_lectivo')

        # Validación de unicidad: no permitir misma sección (nombre) para el mismo grado y año lectivo
        existing = Seccion.query.filter_by(
            id_grado=id_grado,
            id_ano_lectivo=id_ano_lectivo,
            nombre_seccion=nombre_seccion
        ).first()

        if existing:
            flash(f"Ya existe la sección '{nombre_seccion}' para el grado seleccionado en ese año lectivo.", 'danger')
            # Preparar datos para volver a renderizar el formulario con mensaje
            grados = Grado.query.all()
            usuarios = Usuario.query.all()
            anos_lectivos = AnoLectivo.query.filter_by(activo=1).all()
            # Pasar listado simplificado de secciones para validación en frontend
            existing_sections = [
                { 'id_grado': s.id_grado, 'id_ano_lectivo': s.id_ano_lectivo, 'nombre_seccion': s.nombre_seccion }
                for s in Seccion.query.all()
            ]
            return render_template("secciones/nuevo.html",
                                 grados=grados,
                                 usuarios=usuarios,
                                 anos_lectivos=anos_lectivos,
                                 existing_sections=existing_sections)

        nueva = Seccion(
            id_grado=id_grado,
            id_coordinador=id_coordinador,
            nombre_seccion=nombre_seccion,
            id_ano_lectivo=id_ano_lectivo,
            activo=1
        )
        db.session.add(nueva)
        db.session.commit()
        return redirect(url_for('secciones.lista_secciones', success='true', action='created'))
    
    grados = Grado.query.all()
    usuarios = Usuario.query.all()  # Agregado
    anos_lectivos = AnoLectivo.query.filter_by(activo=1).all()
    existing_sections = [
        { 'id_seccion': s.id_seccion, 'id_grado': s.id_grado, 'id_ano_lectivo': s.id_ano_lectivo, 'nombre_seccion': s.nombre_seccion }
        for s in Seccion.query.all()
    ]

    return render_template("secciones/nuevo.html",
                         grados=grados,
                         usuarios=usuarios,  # Agregado
                         anos_lectivos=anos_lectivos,
                         existing_sections=existing_sections)

@secciones_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    grados = Grado.query.all()
    usuarios = Usuario.query.all()
    anos_lectivos = AnoLectivo.query.all()
    
    if request.method == 'POST':
        id_grado = request.form.get('id_grado')
        id_coordinador = request.form.get('id_coordinador')
        nombre_seccion = request.form.get('nombre_seccion').strip().upper()
        id_ano_lectivo = request.form.get('id_ano_lectivo')

        # Validación de unicidad al editar: permitir cambiar otros campos pero no crear duplicado
        duplicate = Seccion.query.filter(
            Seccion.id_grado == id_grado,
            Seccion.id_ano_lectivo == id_ano_lectivo,
            Seccion.nombre_seccion == nombre_seccion,
            Seccion.id_seccion != seccion.id_seccion
        ).first()

        if duplicate:
            flash(f"No puede actualizar: ya existe la sección '{nombre_seccion}' para el grado/año seleccionado.", 'danger')
            grados = Grado.query.all()
            usuarios = Usuario.query.all()
            anos_lectivos = AnoLectivo.query.all()
            return render_template(
                "secciones/editar.html",
                seccion=seccion,
                usuarios=usuarios,
                grados=grados,
                anos_lectivos=anos_lectivos
            )

        seccion.id_grado = id_grado
        seccion.id_coordinador = id_coordinador  # Corregido
        seccion.nombre_seccion = nombre_seccion
        seccion.id_ano_lectivo = id_ano_lectivo
        db.session.commit()
        return redirect(url_for('secciones.lista_secciones', success='true', action='updated'))
    
    existing_sections = [
        { 'id_grado': s.id_grado, 'id_ano_lectivo': s.id_ano_lectivo, 'nombre_seccion': s.nombre_seccion }
        for s in Seccion.query.all()
    ]

    return render_template(
        "secciones/editar.html",
        seccion=seccion,
        usuarios=usuarios,
        grados=grados,
        anos_lectivos=anos_lectivos,
        existing_sections=existing_sections
    )

@secciones_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    db.session.delete(seccion)
    db.session.commit()
    return redirect(url_for('secciones.lista_secciones', success='true', action='deleted'))

# Habilitar sección
@secciones_bp.route('/habilitar/<int:id>', methods=['POST'])
def habilitar_seccion(id):
    seccion = Seccion.query.get_or_404(id)
    seccion.activo = 1
    db.session.commit()
    return redirect(url_for('secciones.lista_secciones', success='true', action='enabled'))

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
    return redirect(url_for('secciones.lista_secciones', success='true', action='disabled'))