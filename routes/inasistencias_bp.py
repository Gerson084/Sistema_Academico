from flask import Blueprint, render_template, request, redirect, url_for, flash

from sqlalchemy import extract
from db import db
from models.Grados import Grado
from models.Estudiantes import Estudiante
from models.Secciones import Seccion
from models.matriculas import Matricula
from models.Inasistencias import Inasistencia
from models.AnosLectivos import AnoLectivo
from datetime import date

inasistencias_bp = Blueprint('inasistencias_bp', __name__, url_prefix='/inasistencias')

@inasistencias_bp.route('/')
def grados():
    grados = Grado.query.all()
    return render_template('inasistencias/grados.html', grados=grados)

@inasistencias_bp.route('/grado/<int:id_grado>')
def estudiantes_grado(id_grado):
    grado = Grado.query.get(id_grado)
    secciones = Seccion.query.filter_by(id_grado=id_grado).all()
    estudiantes = []
    for seccion in secciones:
        matriculas = Matricula.query.filter_by(id_seccion=seccion.id_seccion, activa=True).all()
        for matricula in matriculas:
            estudiante = Estudiante.query.get(matricula.id_estudiante)
            if estudiante:
                estudiantes.append({
                    'estudiante': estudiante,
                    'seccion': seccion
                })
    return render_template('inasistencias/estudiantes.html', estudiantes=estudiantes, grado=grado, secciones=secciones)

@inasistencias_bp.route('/estudiante/<int:id_estudiante>', methods=['GET', 'POST'])
def inasistencias_estudiante(id_estudiante):
    import calendar
    meses = list(range(1, 11))  # Enero a Octubre
    mes = int(request.args.get('mes', date.today().month))
    ano_actual = date.today().year
    estudiante = Estudiante.query.get(id_estudiante)
    ano_lectivo = AnoLectivo.query.filter_by(activo=True).first()
    inasistencias = Inasistencia.query.filter_by(id_estudiante=id_estudiante, id_ano_lectivo=ano_lectivo.id_ano_lectivo).filter(extract('month', Inasistencia.fecha) == mes).all()
    # Obtener el grado actual del estudiante
    matricula = Matricula.query.filter_by(id_estudiante=id_estudiante, activa=True).first()
    id_grado = None
    if matricula:
        seccion = Seccion.query.get(matricula.id_seccion)
        if seccion:
            id_grado = seccion.id_grado
    # Construir matriz de calendario (semanas)
    first_weekday, dias_en_mes = calendar.monthrange(ano_actual, mes)
    # Python: lunes=0, domingo=6. Queremos semanas de lunes a domingo.
    weeks = []
    week = []
    day_counter = 1
    # Rellenar días vacíos al inicio
    for i in range(first_weekday):
        week.append(None)
    while day_counter <= dias_en_mes:
        week.append(day_counter)
        if len(week) == 7:
            weeks.append(week)
            week = []
        day_counter += 1
    # Rellenar días vacíos al final
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)
    return render_template('inasistencias/inasistencias_mes.html', estudiante=estudiante, inasistencias=inasistencias, mes=mes, meses=meses, id_grado=id_grado, weeks=weeks)

@inasistencias_bp.route('/estudiante/<int:id_estudiante>/agregar', methods=['GET', 'POST'])
def agregar_inasistencia(id_estudiante):
    ano_lectivo = AnoLectivo.query.filter_by(activo=True).first()
    if request.method == 'POST':
        fecha = request.form['fecha']
        razon = request.form['razon']
        justificada = bool(int(request.form.get('justificada', 0)))
        nueva_inasistencia = Inasistencia(
            id_estudiante=id_estudiante,
            id_ano_lectivo=ano_lectivo.id_ano_lectivo,
            fecha=fecha,
            razon=razon,
            justificada=justificada
        )
        db.session.add(nueva_inasistencia)
        db.session.commit()
        flash('Inasistencia registrada correctamente.', 'success')
        return redirect(url_for('inasistencias_bp.inasistencias_estudiante', id_estudiante=id_estudiante))
    estudiante = Estudiante.query.get(id_estudiante)
    return render_template('inasistencias/agregar_inasistencia.html', estudiante=estudiante)

@inasistencias_bp.route('/detalle/<int:id_inasistencia>')
def detalle_inasistencia(id_inasistencia):
    inasistencia = Inasistencia.query.get(id_inasistencia)
    return render_template('inasistencias/detalle_inasistencia.html', inasistencia=inasistencia)
