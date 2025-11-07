from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import db
from models.Grados import Grado
from models.Secciones import Seccion
from models.matriculas import Matricula
from models.Estudiantes import Estudiante
from models.Incidentes import Incidente
from models.Periodos import Periodo
from models.usuarios import Usuario
from datetime import datetime

incidentes_bp = Blueprint('incidentes_bp', __name__, url_prefix='/docente/incidentes')


@incidentes_bp.route('/')
def grados():
    grados = Grado.query.all()
    return render_template('docente/incidentes/grados.html', grados=grados)


@incidentes_bp.route('/grado/<int:id_grado>')
def estudiantes_grado(id_grado):
    grado = Grado.query.get(id_grado)
    secciones = Seccion.query.filter_by(id_grado=id_grado).all()

    # Obtener filtros de query string
    seccion_filter = request.args.get('seccion', type=int)
    q = request.args.get('q', '').strip()

    estudiantes = []
    for seccion in secciones:
        # aplicar filtro por sección si se proporcionó
        if seccion_filter and seccion.id_seccion != seccion_filter:
            continue
        matriculas = Matricula.query.filter_by(id_seccion=seccion.id_seccion, activa=True).all()
        for matricula in matriculas:
            estudiante = Estudiante.query.get(matricula.id_estudiante)
            if not estudiante:
                continue
            # filtro por texto: buscar en NIE, nombres o apellidos
            if q:
                ql = q.lower()
                nie = (estudiante.nie or '').lower()
                nombres = (estudiante.nombres or '').lower()
                apellidos = (estudiante.apellidos or '').lower()
                if ql not in nie and ql not in nombres and ql not in apellidos:
                    continue
            estudiantes.append({
                'estudiante': estudiante,
                'seccion': seccion
            })

    return render_template('docente/incidentes/estudiantes.html', estudiantes=estudiantes, grado=grado, secciones=secciones, selected_seccion=seccion_filter, q=q)


@incidentes_bp.route('/estudiante/<int:id_estudiante>')
def incidentes_estudiante(id_estudiante):
    estudiante = Estudiante.query.get(id_estudiante)
    # intentar obtener periodo activo
    periodo = Periodo.query.filter_by(activo=True).first()
    if periodo:
        incidentes = Incidente.query.filter_by(id_estudiante=id_estudiante, id_periodo=periodo.id_periodo).all()
    else:
        incidentes = Incidente.query.filter_by(id_estudiante=id_estudiante).all()
    return render_template('docente/incidentes/incidentes_estudiante.html', estudiante=estudiante, incidentes=incidentes, periodo=periodo)


@incidentes_bp.route('/estudiante/<int:id_estudiante>/agregar', methods=['GET', 'POST'])
def agregar_incidente(id_estudiante):
    estudiante = Estudiante.query.get(id_estudiante)
    periodos = Periodo.query.all()
    if request.method == 'POST':
        fecha_incidente = request.form.get('fecha_incidente')
        hora = request.form.get('hora')
        if hora:
            fecha_str = f"{fecha_incidente} {hora}"
            fecha_incidente_dt = datetime.fromisoformat(fecha_str)
        else:
            fecha_incidente_dt = datetime.fromisoformat(fecha_incidente)

        lugar = request.form.get('lugar')
        tipo_incidente = request.form.get('tipo_incidente')
        descripcion = request.form.get('descripcion')
        medidas_tomadas = request.form.get('medidas_tomadas')
        testigos = request.form.get('testigos')
        id_periodo = int(request.form.get('id_periodo')) if request.form.get('id_periodo') else (Periodo.query.filter_by(activo=True).first().id_periodo if Periodo.query.filter_by(activo=True).first() else None)

        id_reportado_por = session.get('user_id') or request.form.get('id_reportado_por') or 0

        nuevo = Incidente(
            id_estudiante=id_estudiante,
            id_reportado_por=id_reportado_por,
            id_periodo=id_periodo,
            fecha_incidente=fecha_incidente_dt,
            lugar=lugar,
            tipo_incidente=tipo_incidente,
            descripcion=descripcion,
            medidas_tomadas=medidas_tomadas,
            testigos=testigos
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Incidente registrado correctamente.', 'success')
        return redirect(url_for('incidentes_bp.incidentes_estudiante', id_estudiante=id_estudiante))

    return render_template('docente/incidentes/agregar_incidente.html', estudiante=estudiante, periodos=periodos)


@incidentes_bp.route('/detalle/<int:id_incidente>')
def detalle_incidente(id_incidente):
    incidente = Incidente.query.get(id_incidente)
    reportado_por = None
    if incidente and incidente.id_reportado_por:
        reportado_por = Usuario.query.get(incidente.id_reportado_por)
    return render_template('docente/incidentes/detalle_incidente.html', incidente=incidente, reportado_por=reportado_por)


@incidentes_bp.route('/detalle/<int:id_incidente>/imprimir')
def imprimir_incidente(id_incidente):
    """Generar vista imprimible del incidente con espacio de firmas."""
    incidente = Incidente.query.get(id_incidente)
    if not incidente:
        flash('Incidente no encontrado.', 'danger')
        return redirect(url_for('incidentes_bp.grados'))

    reportado_por = Usuario.query.get(incidente.id_reportado_por) if incidente.id_reportado_por else None
    estudiante = Estudiante.query.get(incidente.id_estudiante) if incidente.id_estudiante else None
    periodo = Periodo.query.get(incidente.id_periodo) if incidente.id_periodo else None

    return render_template('docente/incidentes/print_incidente.html', incidente=incidente, reportado_por=reportado_por, estudiante=estudiante, periodo=periodo)
