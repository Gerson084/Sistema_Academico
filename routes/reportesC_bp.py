from flask import Blueprint, render_template, request, session, Response, url_for, redirect
from models.Promedios_periodo import PromedioPeriodo
from models.Promedios_anuales import PromedioAnual
from models.Estudiantes import Estudiante
from models.Grados import Grado
from models.Materias import Materia
from models.Secciones import Seccion
from models.Calificaciones import Calificacion
from models.matriculas import Matricula
from models.MateriaSeccion import MateriaSeccion
from db import db
from datetime import datetime
import io, csv


# Crear Blueprint
reportesC_bp = Blueprint('reportes', __name__, template_folder="templates")

# === REPORTE DE NOTAS POR DOCENTE ===
@reportesC_bp.route('/reporte_notas_docente', methods=['GET'])
def reporte_notas_docente():
    id_docente = session.get('user_id')
    user_role = session.get('user_role')
    if not id_docente or user_role != 2:
        return redirect(url_for('auth.login'))

    # Obtener materias y grados asignados al docente
    asignaciones = MateriaSeccion.query.filter_by(id_maestro=id_docente).all()
    materia_ids = list({a.id_materia for a in asignaciones})
    seccion_ids = list({a.id_seccion for a in asignaciones})
    materias = Materia.query.filter(Materia.id_materia.in_(materia_ids)).all() if materia_ids else []
    grados = Grado.query.join(Grado.secciones).filter(Seccion.id_seccion.in_(seccion_ids)).distinct().all() if seccion_ids else []

    materia_id = request.args.get('materia_id', type=int)
    grado_id = request.args.get('grado_id', type=int)
    estudiantes = None

    if materia_id and grado_id:
        # Buscar secciones del docente que coincidan con materia y grado
        secciones = Seccion.query.filter(
            Seccion.id_grado == grado_id,
            Seccion.id_seccion.in_(seccion_ids)
        ).all()
        seccion_ids_filtradas = [s.id_seccion for s in secciones]
        # Buscar asignaciones válidas
        asigns = MateriaSeccion.query.filter(
            MateriaSeccion.id_maestro == id_docente,
            MateriaSeccion.id_materia == materia_id,
            MateriaSeccion.id_seccion.in_(seccion_ids_filtradas)
        ).all()
        asign_ids = [a.id_asignacion for a in asigns]
        # Buscar estudiantes matriculados en esas secciones
        mats = Matricula.query.filter(
            Matricula.id_seccion.in_(seccion_ids_filtradas),
            Matricula.activa == True
        ).all()
        estudiantes = []
        for m in mats:
            est = m.estudiante
            if not est or not est.activo:
                continue
            # Buscar nota final del último periodo/resumen
            nota_final = None
            resumen = db.session.execute(
                """
                SELECT nota_final_periodo FROM notas_resumen_periodo
                WHERE id_estudiante = :id_est AND id_asignacion IN :asign_ids
                ORDER BY id_periodo DESC LIMIT 1
                """,
                {'id_est': est.id_estudiante, 'asign_ids': tuple(asign_ids) if asign_ids else (0,)}
            ).first()
            if resumen:
                nota_final = resumen.nota_final_periodo
            estudiantes.append({
                'nie': est.nie,
                'nombre_completo': f"{est.apellidos}, {est.nombres}",
                'nota_final': nota_final if nota_final is not None else '-'
            })

    return render_template(
        'reportesC/reporte_notas_docente.html',
        materias=materias,
        grados=grados,
        materia_id=materia_id,
        grado_id=grado_id,
        estudiantes=estudiantes
    )

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
        # Reporte detallado de estudiante (campos conducta/actitud eliminados)
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
    # columna Nota Actitud eliminada

    periodos = PromedioPeriodo.query.join(PromedioPeriodo.calificacion).filter(Calificacion.id_estudiante == estudiante_id)
    if asign_ids:
        periodos = periodos.filter(Calificacion.id_asignacion.in_(asign_ids))
    periodos = periodos.order_by(PromedioPeriodo.fecha_calculo.desc()).all()
    for p in periodos:
        periodo_nombre = p.calificacion.periodo.nombre if p.calificacion and p.calificacion.periodo else p.calificacion.id_periodo if p.calificacion else '-'
    # columna Nota Actitud eliminada

    writer.writerow([])
    writer.writerow(['Promedios Anuales'])
    writer.writerow(['Periodo', 'Fecha Calculo', 'Promedio Final', 'Estado'])
    anuales = PromedioAnual.query.join(PromedioAnual.promedio_periodo).join(PromedioPeriodo.calificacion).filter(Calificacion.id_estudiante == estudiante_id)
    if asign_ids:
        anuales = anuales.filter(Calificacion.id_asignacion.in_(asign_ids))
    anuales = anuales.order_by(PromedioAnual.fecha_calculo.desc()).all()
    for a in anuales:
        periodo_nombre = a.periodo.nombre if a.periodo else a.id_periodo
        # columna conducta_final eliminada

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
        # Genera PDF del reporte del estudiante (campos conducta/actitud eliminados)
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

   