# routes/reportesC_bp.py
from flask import Blueprint, render_template, request, session, Response, url_for, redirect
from models.Promedios_periodo import PromedioPeriodo
from models.Promedios_anuales import PromedioAnual
from models.Estudiantes import Estudiante
from models.Grados import Grado
from models.Secciones import Seccion
from models.Calificaciones import Calificacion
from models.matriculas import Matricula
from models.MateriaSeccion import MateriaSeccion
from db import db
from datetime import datetime
import io, csv


# Crear Blueprint
reportesC_bp = Blueprint('reportes', __name__, template_folder="templates")

# ==============================
# REPORTE DE PROMEDIO POR PERIODO
# ==============================
@reportesC_bp.route('/reporte_conducta_periodo', methods=['GET'])
def reporte_conducta_periodo():
    grado_id = request.args.get('grado_id', type=int)
    seccion_id = request.args.get('seccion_id', type=int)
    periodo_id = request.args.get('periodo_id', type=int)

    query = PromedioPeriodo.query.join(PromedioPeriodo.calificacion).join('estudiante').join('matricula')  # si quieres filtrar por sección/grado

    # Si el usuario en sesión es docente, limitar a sus asignaciones (materia+sección)
    id_docente = session.get('user_id')
    user_role = session.get('user_role')
    if id_docente and user_role == 2:
        asignaciones = MateriaSeccion.query.filter_by(id_maestro=id_docente).all()
        asign_ids = [a.id_asignacion for a in asignaciones]
        if asign_ids:
            query = query.join(Calificacion).filter(Calificacion.id_asignacion.in_(asign_ids))
        else:
            # docente sin asignaciones: no resultados
            resultados = []
            grados = Grado.query.all()
            secciones = Seccion.query.all()
            return render_template('reportesC/promedio_periodo.html', resultados=resultados, grados=grados, secciones=secciones, grado_id=grado_id, seccion_id=seccion_id, periodo_id=periodo_id)

    if grado_id:
        query = query.join('matricula').join('seccion').filter(Seccion.id_grado == grado_id)
    if seccion_id:
        query = query.join('matricula').join('seccion').filter(Seccion.id_seccion == seccion_id)
    if periodo_id:
        query = query.join('calificacion').filter(Calificacion.id_periodo == periodo_id)

    resultados = query.all()

    grados = Grado.query.all()
    secciones = Seccion.query.all()

    return render_template(
        'reportesC/promedio_periodo.html',
        resultados=resultados,
        grados=grados,
        secciones=secciones,
        grado_id=grado_id,
        seccion_id=seccion_id,
        periodo_id=periodo_id
    )


@reportesC_bp.route('/reporte_conducta_estudiante', methods=['GET'])
def reporte_conducta_estudiante():
    """Reporte detallado de conducta/actitud de un estudiante.
    Parámetros GET:
      - estudiante_id (int): id del estudiante
      - periodo_id (opcional): filtrar promedios_periodo por periodo
    """
    estudiante_id = request.args.get('estudiante_id', type=int)
    periodo_id = request.args.get('periodo_id', type=int)

    # Obtener contexto de docente en sesión
    id_docente = session.get('user_id')
    user_role = session.get('user_role')

    # Si no se indicó estudiante_id, mostramos el formulario con filtros (grados/secciones del docente)
    if not estudiante_id:
        assigned_grados = []
        assigned_secciones = []
        # Si es docente, obtener sólo sus asignaciones
        if id_docente and user_role == 2:
            asignaciones = MateriaSeccion.query.filter_by(id_maestro=id_docente).all()
            seccion_ids = list({a.id_seccion for a in asignaciones})
            if seccion_ids:
                assigned_secciones = Seccion.query.filter(Seccion.id_seccion.in_(seccion_ids)).all()
                grado_ids = list({s.id_grado for s in assigned_secciones})
                assigned_grados = Grado.query.filter(Grado.id_grado.in_(grado_ids)).all()
        else:
            # Para otros roles mostrar todos por defecto
            assigned_grados = Grado.query.all()
            assigned_secciones = Seccion.query.all()

        # Si vienen filtros, listar estudiantes
        grado_id = request.args.get('grado_id', type=int)
        seccion_id = request.args.get('seccion_id', type=int)

        estudiantes_list = []
        if seccion_id:
            # Verificar que el docente tiene acceso a esta sección (si es docente)
            if id_docente and user_role == 2:
                has_access = MateriaSeccion.query.filter_by(id_maestro=id_docente, id_seccion=seccion_id).first()
                if not has_access:
                    return render_template('reportesC/reporte_conducta_estudiante.html', estudiante=None, periodos=[], anuales=[], estudiante_not_found=False, acceso_denegado=True, estudiante_id=None, assigned_grados=assigned_grados, assigned_secciones=assigned_secciones, estudiantes_list=[], override_role=2 if user_role==2 else None)

            # Obtener estudiantes matriculados en la sección
            mats = Matricula.query.filter_by(id_seccion=seccion_id, activa=True).all()
            for m in mats:
                if not m.estudiante or not m.estudiante.activo:
                    continue
                estudiantes_list.append(m.estudiante)

        return render_template('reportesC/reporte_conducta_estudiante.html', estudiante=None, periodos=[], anuales=[], estudiante_not_found=False, acceso_denegado=False, estudiante_id=None, assigned_grados=assigned_grados, assigned_secciones=assigned_secciones, estudiantes_list=estudiantes_list, override_role=2 if user_role==2 else None)

    # Intentar obtener el estudiante
    estudiante = Estudiante.query.get(estudiante_id)
    if not estudiante:
        return render_template('reportesC/reporte_conducta_estudiante.html', estudiante=None, periodos=[], anuales=[], estudiante_not_found=True, estudiante_id=estudiante_id, override_role=2 if user_role==2 else None)

    # Si el usuario en sesión es docente, verificar que el estudiante pertenezca a al menos una de sus asignaciones
    acceso_permitido = True
    asign_ids = None
    if id_docente and user_role == 2:
        asignaciones = MateriaSeccion.query.filter_by(id_maestro=id_docente).all()
        asign_ids = [a.id_asignacion for a in asignaciones]
        if not asign_ids:
            acceso_permitido = False
        else:
            # Comprobar si existen promedios del estudiante en esas asignaciones
            existe = db.session.query(PromedioPeriodo).join(PromedioPeriodo.calificacion).filter(
                Calificacion.id_estudiante == estudiante_id,
                Calificacion.id_asignacion.in_(asign_ids)
            ).first()
            if not existe:
                acceso_permitido = True

    if not acceso_permitido:
        return render_template('reportesC/reporte_conducta_estudiante.html', estudiante=None, periodos=[], anuales=[], estudiante_not_found=False, acceso_denegado=True, estudiante_id=estudiante_id, override_role=2 if user_role==2 else None)

    # Promedios por periodo para el estudiante
    query_periodos = PromedioPeriodo.query.join(PromedioPeriodo.calificacion).filter(
        Calificacion.id_estudiante == estudiante_id
    )
    if periodo_id:
        query_periodos = query_periodos.filter(Calificacion.id_periodo == periodo_id)

    # Si docente: limitar por asignaciones
    if asign_ids:
        query_periodos = query_periodos.filter(Calificacion.id_asignacion.in_(asign_ids))

    periodos = query_periodos.order_by(PromedioPeriodo.fecha_calculo.desc()).all()

    # Promedios anuales relacionados a través de PromedioPeriodo -> Calificacion -> Estudiante
    anuales = PromedioAnual.query.join(PromedioAnual.promedio_periodo).join(PromedioPeriodo.calificacion).filter(
        Calificacion.id_estudiante == estudiante_id
    )
    if asign_ids:
        anuales = anuales.filter(Calificacion.id_asignacion.in_(asign_ids))
    anuales = anuales.order_by(PromedioAnual.fecha_calculo.desc()).all()

    return render_template(
        'reportesC/reporte_conducta_estudiante.html',
        estudiante=estudiante,
        periodos=periodos,
        anuales=anuales,
        estudiante_not_found=False,
        override_role=2 if user_role==2 else None
    )


@reportesC_bp.route('/reporte_conducta_estudiante/download', methods=['GET'])
def reporte_conducta_estudiante_download():
    estudiante_id = request.args.get('estudiante_id', type=int)
    if not estudiante_id:
        return redirect(url_for('reportes.reporte_conducta_estudiante'))

    # Verificar permisos (mismo control que en la vista)
    id_docente = session.get('user_id')
    user_role = session.get('user_role')
    asign_ids = None
    if id_docente and user_role == 2:
        asignaciones = MateriaSeccion.query.filter_by(id_maestro=id_docente).all()
        asign_ids = [a.id_asignacion for a in asignaciones]
        if not asign_ids:
            return "Acceso denegado", 403
        existe = db.session.query(PromedioPeriodo).join(PromedioPeriodo.calificacion).filter(
            Calificacion.id_estudiante == estudiante_id,
            Calificacion.id_asignacion.in_(asign_ids)
        ).first()
        if not existe:
            return "Acceso denegado", 403

    estudiante = Estudiante.query.get(estudiante_id)
    if not estudiante:
        return "Estudiante no encontrado", 404

    # Construir CSV: periodos y promedios anuales
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Estudiante', estudiante.nie, f"{estudiante.nombres} {estudiante.apellidos}"])
    writer.writerow([])
    writer.writerow(['Promedios por Periodo'])
    writer.writerow(['Periodo', 'Fecha Calculo', 'Nota Actitud'])

    periodos = PromedioPeriodo.query.join(PromedioPeriodo.calificacion).filter(Calificacion.id_estudiante == estudiante_id)
    if asign_ids:
        periodos = periodos.filter(Calificacion.id_asignacion.in_(asign_ids))
    periodos = periodos.order_by(PromedioPeriodo.fecha_calculo.desc()).all()
    for p in periodos:
        periodo_nombre = p.calificacion.periodo.nombre if p.calificacion and p.calificacion.periodo else p.calificacion.id_periodo if p.calificacion else '-'
        writer.writerow([periodo_nombre, p.fecha_calculo.strftime('%Y-%m-%d') if p.fecha_calculo else '-', p.nota_actitud])

    writer.writerow([])
    writer.writerow(['Promedios Anuales'])
    writer.writerow(['Periodo', 'Fecha Calculo', 'Promedio Final', 'Conducta Final', 'Estado'])
    anuales = PromedioAnual.query.join(PromedioAnual.promedio_periodo).join(PromedioPeriodo.calificacion).filter(Calificacion.id_estudiante == estudiante_id)
    if asign_ids:
        anuales = anuales.filter(Calificacion.id_asignacion.in_(asign_ids))
    anuales = anuales.order_by(PromedioAnual.fecha_calculo.desc()).all()
    for a in anuales:
        periodo_nombre = a.periodo.nombre if a.periodo else a.id_periodo
        writer.writerow([periodo_nombre, a.fecha_calculo.strftime('%Y-%m-%d') if a.fecha_calculo else '-', float(a.promedio_final) if a.promedio_final else '', a.conducta_final, a.estado_final])

    output.seek(0)
    csv_data = output.getvalue()
    output.close()

    headers = {
        'Content-Disposition': f'attachment; filename=reportes_conducta_estudiante_{estudiante_id}.csv',
        'Content-Type': 'text/csv; charset=utf-8'
    }
    return Response(csv_data, headers=headers)

# ==============================
# REPORTE DE PROMEDIO ANUAL
# ==============================
@reportesC_bp.route('/promedio_anual', methods=['GET'])
def promedio_anual():
    grado_id = request.args.get('grado_id', type=int)
    seccion_id = request.args.get('seccion_id', type=int)

    query = PromedioAnual.query

    if grado_id:
        query = query.join(Estudiante).join(Seccion).filter(Seccion.id_grado == grado_id)
    if seccion_id:
        query = query.join(Seccion).filter(Seccion.id_seccion == seccion_id)

    resultados = query.all()

    grados = Grado.query.all()
    secciones = Seccion.query.all()

    return render_template(
        'reportesC/promedio_anual.html',
        resultados=resultados,
        grados=grados,
        secciones=secciones,
        grado_id=grado_id,
        seccion_id=seccion_id
    )


@reportesC_bp.route('/reporte_conducta_estudiante/pdf', methods=['GET'])
def reporte_conducta_estudiante_pdf():
    """Genera PDF del reporte de conducta del estudiante.
    Parámetros GET:
      - estudiante_id (int): id del estudiante
      - tipo (string): 'periodo', 'anual' o 'completo'
    """
    estudiante_id = request.args.get('estudiante_id', type=int)
    tipo_reporte = request.args.get('tipo', 'completo')  # periodo, anual, completo
    
    if not estudiante_id:
        return "Estudiante no especificado", 400

    # Verificar permisos (mismo control que en la vista)
    id_docente = session.get('user_id')
    user_role = session.get('user_role')
    asign_ids = None
    
    if id_docente and user_role == 2:
        asignaciones = MateriaSeccion.query.filter_by(id_maestro=id_docente).all()
        asign_ids = [a.id_asignacion for a in asignaciones]
        if not asign_ids:
            return "Acceso denegado", 403
        
        # Verificar por matrícula
        seccion_ids = list({a.id_seccion for a in asignaciones})
        existe = Matricula.query.filter(
            Matricula.id_estudiante == estudiante_id,
            Matricula.id_seccion.in_(seccion_ids),
            Matricula.activa == True
        ).first()
        
        if not existe:
            return "Acceso denegado", 403

    estudiante = Estudiante.query.get(estudiante_id)
    if not estudiante:
        return "Estudiante no encontrado", 404

    # Obtener promedios por periodo
    query_periodos = PromedioPeriodo.query.join(PromedioPeriodo.calificacion).filter(
        Calificacion.id_estudiante == estudiante_id
    )
    if asign_ids:
        query_periodos = query_periodos.filter(Calificacion.id_asignacion.in_(asign_ids))
    periodos = query_periodos.order_by(PromedioPeriodo.fecha_calculo.desc()).all()

    # Obtener promedios anuales
    anuales = PromedioAnual.query.join(PromedioAnual.promedio_periodo).join(PromedioPeriodo.calificacion).filter(
        Calificacion.id_estudiante == estudiante_id
    )
    if asign_ids:
        anuales = anuales.filter(Calificacion.id_asignacion.in_(asign_ids))
    anuales = anuales.order_by(PromedioAnual.fecha_calculo.desc()).all()

    # Renderizar template HTML para PDF
    html_string = render_template(
        'reportesC/reporte_conducta_pdf.html',
        estudiante=estudiante,
        periodos=periodos,
        anuales=anuales,
        tipo_reporte=tipo_reporte
    )

   