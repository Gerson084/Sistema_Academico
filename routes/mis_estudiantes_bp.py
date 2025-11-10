from flask import Blueprint, render_template, request, session, send_file, url_for, redirect, flash
from models.MateriaSeccion import MateriaSeccion
from models.Secciones import Seccion
from models.Grados import Grado
from models.Estudiantes import Estudiante
from models.matriculas import Matricula
from models.Promedios_periodo import PromedioPeriodo
from models.Promedios_anuales import PromedioAnual
from models.Calificaciones import Calificacion
from models.Materias import Materia
from models.Periodos import Periodo
from models.ConductaGrado import ConductaGradoPeriodo
from models.Inasistencias import Inasistencia
from db import db
import io
from flask import current_app
import os
import datetime
from sqlalchemy import extract, text

mis_estudiantes_bp = Blueprint('mis_estudiantes', __name__, template_folder='templates')

@mis_estudiantes_bp.route('/mis-estudiantes')
def mis_estudiantes():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    estudiantes = []
    secciones_list = []
    materias_list = []
    
    if user_role == 2:  # Docente
        # Obtener asignaciones del docente
        asignaciones = MateriaSeccion.query.filter_by(id_maestro=user_id).all()
        for asignacion in asignaciones:
            matriculas = Matricula.query.filter_by(id_seccion=asignacion.id_seccion, activa=True).all()
            for m in matriculas:
                estudiante = Estudiante.query.get(m.id_estudiante)
                if estudiante:
                    estudiantes.append({
                        'estudiante': estudiante,
                        'grado': asignacion.seccion.grado.nombre_grado,
                        'seccion': asignacion.seccion.nombre_seccion,
                        'id_seccion': asignacion.id_seccion,
                        'materia': asignacion.materia.nombre_materia,
                        'id_materia': getattr(asignacion.materia, 'id_materia', None),
                        'id_asignacion': asignacion.id_asignacion
                    })
        # Listar materias impartidas por el docente
        materias_list = [ { 'id': a.materia.id_materia, 'nombre': a.materia.nombre_materia } for a in asignaciones if getattr(a, 'materia', None) ]
    
    elif user_role == 1:  # Coordinador
        # Obtener todas las secciones que coordina
        secciones = Seccion.query.filter_by(id_coordinador=user_id, activo=True).all()
        for seccion in secciones:
            matriculas = Matricula.query.filter_by(id_seccion=seccion.id_seccion, activa=True).all()
            for m in matriculas:
                estudiante = Estudiante.query.get(m.id_estudiante)
                if estudiante:
                    estudiantes.append({
                        'estudiante': estudiante,
                        'grado': seccion.grado.nombre_grado,
                        'seccion': seccion.nombre_seccion,
                        'id_seccion': seccion.id_seccion,
                        'materia': None,  # Coordinador ve todas las materias
                        'id_materia': None,
                        'id_asignacion': 0  # 0 indica ver todas las materias
                    })
        # Opcional: listar secciones que coordina y materias en esas secciones
        secciones_list = [ { 'id': s.id_seccion, 'nombre': s.nombre_seccion } for s in secciones ]
        # Materias existentes en esas secciones (distinct)
        materias_query = MateriaSeccion.query.filter(MateriaSeccion.id_seccion.in_([s.id_seccion for s in secciones])).all() if secciones else []
        materias_list = [ { 'id': m.materia.id_materia, 'nombre': m.materia.nombre_materia } for m in materias_query if getattr(m, 'materia', None) ]

    # Eliminar duplicados basados en el ID del estudiante
    estudiantes_unicos = {}
    for e in estudiantes:
        key = e['estudiante'].id_estudiante
        if key not in estudiantes_unicos:
            estudiantes_unicos[key] = e
    
    return render_template('mis_estudiantes/lista.html', 
                         estudiantes=list(estudiantes_unicos.values()),
                         user_role=user_role,
                         secciones=secciones_list,
                         materias=materias_list)


@mis_estudiantes_bp.route('/ver-boleta/<int:id_estudiante>/<int:id_asignacion>')
def ver_boleta(id_estudiante, id_asignacion):
    # Usaremos la función helper para preparar el contexto y renderizar
    contexto = _preparar_contexto_boleta(id_estudiante, id_asignacion)
    if contexto is None:
        flash('No se encontró matrícula activa para el estudiante.', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))

    return render_template('mis_estudiantes/boleta.html', **contexto)

@mis_estudiantes_bp.route('/descargar-boleta/<int:id_estudiante>/<int:id_asignacion>')
def descargar_boleta(id_estudiante, id_asignacion):
    # Preparar contexto usando la misma lógica que la vista de previsualización
    contexto = _preparar_contexto_boleta(id_estudiante, id_asignacion)
    if contexto is None:
        flash('No se encontró matrícula activa para el estudiante.', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))

    # Renderizar HTML exactamente igual que la vista
    html = render_template('mis_estudiantes/boleta.html', **contexto)

    try:
        import pdfkit

        # Configuración mejorada para pdfkit/wkhtmltopdf
        options = {
            'page-size': 'A4',
            'margin-top': '5mm',
            'margin-right': '5mm',
            'margin-bottom': '5mm',
            'margin-left': '5mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
            'disable-smart-shrinking': None,
            'print-media-type': None,
            'dpi': 300
        }

        # Intentar usar la ruta configurada de wkhtmltopdf primero
        try:
            wk_path = current_app.config.get('WKHTMLTOPDF_PATH')
            if wk_path:
                config = pdfkit.configuration(wkhtmltopdf=wk_path)
                pdf = pdfkit.from_string(html, False, configuration=config, options=options)
            else:
                pdf = pdfkit.from_string(html, False, options=options)
        except Exception as e:
            # Si hay un error, intentar con WeasyPrint
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration

                # Configurar fuentes para WeasyPrint
                font_config = FontConfiguration()
                pdf = HTML(string=html).write_pdf(
                    stylesheets=[
                        CSS(string='''
                            @page {
                                size: A4;
                                margin: 5mm;
                            }
                            body {
                                font-family: "Segoe UI", sans-serif;
                            }
                        ''', font_config=font_config)
                    ],
                    font_config=font_config
                )
            except Exception as weasy_error:
                # Si ambos fallan, usar la solución más simple con ReportLab
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.lib import colors
                from reportlab.lib.units import mm

                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                width, height = A4

                # Header
                c.setFont('Helvetica-Bold', 16)
                c.drawCentredString(width/2, height-30*mm, 'Boleta de Notas')

                # Información del estudiante
                c.setFont('Helvetica', 12)
                y = height - 50*mm
                c.drawString(20*mm, y, f"Estudiante: {contexto['estudiante'].nombres} {contexto['estudiante'].apellidos}")
                y -= 10*mm
                c.drawString(20*mm, y, f"NIE: {contexto['estudiante'].nie}")
                y -= 10*mm
                c.drawString(20*mm, y, f"Grado: {contexto['seccion'].grado.nombre_grado} - {contexto['seccion'].nombre_seccion}")

                # Notas
                y -= 20*mm
                c.setFont('Helvetica-Bold', 10)
                headers = ['Materia', 'P1', 'P2', 'P3', 'P4', 'Final']
                x = 20*mm
                for header in headers:
                    c.drawString(x, y, header)
                    x += 30*mm

                y -= 10*mm
                c.setFont('Helvetica', 10)
                for materia in contexto['materias']:
                    if y < 30*mm:  # Nueva página si no hay espacio
                        c.showPage()
                        y = height - 30*mm
                        c.setFont('Helvetica', 10)

                    x = 20*mm
                    c.drawString(x, y, str(materia['nombre_materia']))
                    x += 30*mm
                    for periodo in ['periodo1', 'periodo2', 'periodo3', 'periodo4']:
                        c.drawString(x, y, str(materia[periodo]))
                        x += 30*mm
                    c.drawString(x, y, str(materia['final']))
                    y -= 10*mm

                # Conducta si existe
                y -= 15*mm
                if contexto.get('conducta'):
                    c.drawString(20*mm, y, f"Conducta: {getattr(contexto['conducta'], 'nota_conducta_final', '--')} ({getattr(contexto['conducta'], 'conducta_literal', '--')})")
                    if getattr(contexto['conducta'], 'observacion_general', None):
                        y -= 10*mm
                        c.drawString(20*mm, y, f"Observación: {contexto['conducta'].observacion_general}")

                c.showPage()
                c.save()
                pdf = buffer.getvalue()
                buffer.close()

        # Enviar el PDF generado
        return send_file(
            io.BytesIO(pdf),
            download_name=f"boleta_{contexto['estudiante'].nie}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Error al generar el PDF: {str(e)}', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))


def _obtener_inasistencias(id_estudiante, id_seccion, ano_lectivo):
    """Obtiene las inasistencias del estudiante por mes."""
    inasistencias = Inasistencia.query.filter_by(
        id_estudiante=id_estudiante,
        id_ano_lectivo=ano_lectivo
    ).all()

    faltas_por_mes = {
        'ene': 0, 'feb': 0, 'mar': 0, 'abr': 0, 
        'may': 0, 'jun': 0, 'jul': 0, 'ago': 0, 
        'sep': 0, 'oct': 0, 'nov': 0, 'dic': 0
    }

    for inasistencia in inasistencias:
        mes = inasistencia.fecha.month
        mes_str = list(faltas_por_mes.keys())[mes - 1]
        faltas_por_mes[mes_str] += 1

    faltas_por_mes['total'] = sum(faltas_por_mes.values())
    return faltas_por_mes

def _obtener_notas_materia(id_estudiante, id_asignacion, periodos):
    """Obtiene las notas de una materia específica para todos los períodos."""
    notas_periodos = []
    notas_validas = []

    for periodo in periodos:
        # Primero intentar obtener el promedio periodal almacenado en la tabla
        # `promedios_periodo` (modelo `PromedioPeriodo`) vinculado a una calificación.
        nota_encontrada = None
        calificacion = Calificacion.query.filter_by(
            id_estudiante=id_estudiante,
            id_asignacion=id_asignacion,
            id_periodo=periodo.id_periodo
        ).first()

        if calificacion:
            promedio_periodo = PromedioPeriodo.query.filter_by(
                id_calificacion=calificacion.id_calificacion
            ).first()

            if promedio_periodo and promedio_periodo.nota_final_periodo is not None:
                nota_encontrada = float(promedio_periodo.nota_final_periodo)

        # Si no hay registro en `promedios_periodo`, intentar la tabla `notas_resumen_periodo`
        # (esta tabla es la que se usa en `guardar_notas` y puede contener el resumen final por periodo)
        if nota_encontrada is None:
            try:
                sql = text(
                    "SELECT nota_final_periodo, promedio FROM notas_resumen_periodo "
                    "WHERE id_estudiante = :id_estudiante "
                    "AND id_asignacion = :id_asignacion "
                    "AND id_periodo = :id_periodo LIMIT 1"
                )
                r = db.session.execute(sql, {
                    'id_estudiante': id_estudiante,
                    'id_asignacion': id_asignacion,
                    'id_periodo': periodo.id_periodo
                }).first()

                if r is not None:
                    # r puede ser Row o tupla; intentar obtener por índice o por nombre
                    try:
                        val = r['nota_final_periodo'] if 'nota_final_periodo' in r.keys() else r[0]
                    except Exception:
                        # fallback a índice 0
                        val = r[0] if len(r) > 0 else None

                    if val is not None:
                        nota_encontrada = float(val)
            except Exception:
                # Si falla la consulta raw, no rompemos la vista; dejamos nota_encontrada = None
                nota_encontrada = None

        # Si aún no hay nota encontrada, calcular promedio simple a partir de las calificaciones individuales
        if nota_encontrada is None:
            try:
                califs = Calificacion.query.filter_by(
                    id_estudiante=id_estudiante,
                    id_asignacion=id_asignacion,
                    id_periodo=periodo.id_periodo
                ).all()
                if califs:
                    suma = 0.0
                    cuenta = 0
                    for c in califs:
                        try:
                            suma += float(c.nota)
                            cuenta += 1
                        except Exception:
                            continue
                    if cuenta > 0:
                        nota_encontrada = suma / cuenta
            except Exception:
                # Si falla, dejamos nota_encontrada = None
                nota_encontrada = None

        if nota_encontrada is not None:
            notas_periodos.append(nota_encontrada)
            notas_validas.append(nota_encontrada)
        else:
            notas_periodos.append('--')

    # Calcular promedios
    while len(notas_periodos) < 4:  # Asegurar 4 períodos
        notas_periodos.append('--')

    promedio = sum(notas_validas) / len(notas_validas) if notas_validas else '--'
    trimestre = sum(notas_validas[:3]) / len(notas_validas[:3]) if len(notas_validas) >= 3 else '--'
    examen = notas_validas[3] if len(notas_validas) > 3 else '--'

    # Intentar obtener 'actitud'/aptitud desde la tabla conducta_materia_periodo si existe
    actitud_val = None
    try:
        sql_act = text(
            "SELECT * FROM conducta_materia_periodo "
            "WHERE id_estudiante = :id_estudiante "
            "AND id_asignacion = :id_asignacion LIMIT 1"
        )
        r_act = db.session.execute(sql_act, {
            'id_estudiante': id_estudiante,
            'id_asignacion': id_asignacion
        }).first()
        if r_act is not None:
            # Buscar campos habituales que pueden contener la nota de actitud
            keys = []
            try:
                keys = list(r_act.keys())
            except Exception:
                # r_act puede ser una tupla; en ese caso no hay keys
                keys = []

            posibles = ['nota_actitud', 'actitud', 'aptitud', 'nota', 'calificacion_actitud', 'nota_actitud_final']
            found = None
            if keys:
                for p in posibles:
                    if p in keys:
                        found = r_act[p]
                        break
            else:
                # intentar por índices comunes
                try:
                    # si hay al menos 1 columna, usar la última columna como posible actitud
                    found = r_act[-1]
                except Exception:
                    found = None

            if found is not None:
                try:
                    actitud_val = float(found)
                except Exception:
                    actitud_val = str(found)
    except Exception:
        actitud_val = None

    return {
        'notas_periodos': notas_periodos,
        'promedio': promedio,
        'trimestre': trimestre,
        'examen': examen,
        'actitud': actitud_val if actitud_val is not None else '--'
    }

def _preparar_contexto_boleta(id_estudiante, id_asignacion):
    """Prepara el contexto completo para la boleta de calificaciones."""
    # Verificar permisos
    user_role = session.get('user_role')
    user_id = session.get('user_id')

    estudiante = Estudiante.query.get_or_404(id_estudiante)
    matricula = Matricula.query.filter_by(id_estudiante=id_estudiante, activa=True).first()
    
    if not matricula:
        return None

    # Verificar permisos según el rol
    if user_role == 2:  # Docente
        if id_asignacion != 0:
            asignacion = MateriaSeccion.query.get(id_asignacion)
            if not asignacion or asignacion.id_maestro != user_id:
                flash('No tiene permiso para ver esta boleta', 'danger')
                return None
    elif user_role == 1:  # Coordinador
        seccion = Seccion.query.get(matricula.id_seccion)
        if seccion.id_coordinador != user_id:
            flash('No tiene permiso para ver esta boleta', 'danger')
            return None

    # Obtener períodos del año lectivo
    periodos = Periodo.query.filter_by(
        id_ano_lectivo=matricula.seccion.id_ano_lectivo
    ).order_by(Periodo.numero_periodo).all()

    # Obtener materias según el rol y asignación
    if id_asignacion and id_asignacion != 0:
        asignaciones = [MateriaSeccion.query.get_or_404(id_asignacion)]
    else:
        asignaciones = MateriaSeccion.query.filter_by(
            id_seccion=matricula.id_seccion
        ).order_by(MateriaSeccion.id_asignacion).all()

    # Determinar esquema de columnas dinámico según el grado
    # Regla propuesta: si el nivel o nombre del grado contiene 'bachiller' => usar periodos (1°P..4°P)
    # Caso contrario (Parvularia a 9°) => usar esquema trimestre/examen (TRIM + EXAMEN)
    nombre_grado_lower = matricula.seccion.grado.nombre_grado.lower()
    nivel_lower = (matricula.seccion.grado.nivel or '').lower()
    # Si no es bachillerato, consideramos "nivel básico" (Parvularia a 9°) => trimestres
    esquema = 'periodos' if ('bachiller' in nombre_grado_lower or 'bachiller' in nivel_lower) else 'trimestres'

    # Procesar cada materia
    materias_data = []
    for asig in asignaciones:
        notas_info = _obtener_notas_materia(id_estudiante, asig.id_asignacion, periodos)
        
        if esquema == 'periodos':
            # Bachillerato: mostrar los 4 periodos tal cual
            final_calc = notas_info['promedio']
            materia_info = {
                'nombre_materia': asig.materia.nombre_materia,
                'actitud': format(notas_info['actitud'], '.1f') if isinstance(notas_info.get('actitud'), float) else (notas_info.get('actitud') or '--'),
                'periodo1': format(notas_info['notas_periodos'][0], '.1f') if isinstance(notas_info['notas_periodos'][0], float) else '--',
                'periodo2': format(notas_info['notas_periodos'][1], '.1f') if isinstance(notas_info['notas_periodos'][1], float) else '--',
                'periodo3': format(notas_info['notas_periodos'][2], '.1f') if isinstance(notas_info['notas_periodos'][2], float) else '--',
                'periodo4': format(notas_info['notas_periodos'][3], '.1f') if isinstance(notas_info['notas_periodos'][3], float) else '--',
                'final': format(final_calc, '.1f') if isinstance(final_calc, float) else '--'
            }
        else:
            # Nivel básico: 3 trimestres (sin columna de examen)
            tri_vals = []
            campos = {}
            for i in range(3):
                val = notas_info['notas_periodos'][i] if i < len(notas_info['notas_periodos']) else '--'
                campos[f'trim{i+1}'] = format(val, '.1f') if isinstance(val, float) else '--'
                if isinstance(val, float):
                    tri_vals.append(val)
            final_tri = sum(tri_vals)/len(tri_vals) if tri_vals else '--'
            materia_info = {
                'nombre_materia': asig.materia.nombre_materia,
                'actitud': format(notas_info['actitud'], '.1f') if isinstance(notas_info.get('actitud'), float) else (notas_info.get('actitud') or '--'),
                **campos,
                'final': format(final_tri, '.1f') if isinstance(final_tri, float) else '--'
            }
        materias_data.append(materia_info)

    # Calcular promedio global
    notas_finales = [float(m['final']) for m in materias_data if m['final'] != '--']
    promedio_global = format(sum(notas_finales)/len(notas_finales), '.1f') if notas_finales else '--'

    # Obtener conducta
    conducta = ConductaGradoPeriodo.query.filter_by(
        id_estudiante=id_estudiante,
        id_seccion=matricula.id_seccion,
        id_ano_lectivo=matricula.seccion.id_ano_lectivo
    ).first()

    # Obtener inasistencias
    faltas = _obtener_inasistencias(
        id_estudiante, 
        matricula.id_seccion,
        matricula.seccion.id_ano_lectivo
    )

    # Datos de escuela de padres (implementar según necesidad)
    esc_padres = {'p1': 'SI', 'p2': 'SI', 'p3': '-', 'p4': '-'}

    return {
        'estudiante': estudiante,
        'seccion': matricula.seccion,
        'asignacion': asignaciones[0] if len(asignaciones) == 1 else None,
        'materias': materias_data,
        'promedio_global': promedio_global,
        'faltas': faltas,
        'esc_padres': esc_padres,
        'ano_lectivo': matricula.seccion.ano_lectivo,
        'fecha_actual': datetime.datetime.now().strftime('%d/%m/%Y'),
        'conducta': conducta,
        'periodos': periodos,
        'esquema': esquema
    }
