from flask import Blueprint, render_template, request, session, send_file, url_for, redirect
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
from db import db
import io
from flask import flash
from flask import current_app
import os
import datetime

mis_estudiantes_bp = Blueprint('mis_estudiantes', __name__, template_folder='templates')

@mis_estudiantes_bp.route('/mis-estudiantes')
def mis_estudiantes():
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    estudiantes = []
    if user_role == 2:  # Docente
        asignaciones = MateriaSeccion.query.filter_by(id_maestro=user_id).all()
        for asignacion in asignaciones:
            matriculas = Matricula.query.filter_by(id_seccion=asignacion.id_seccion, activa=True).all()
            for m in matriculas:
                estudiante = Estudiante.query.get(m.id_estudiante)
                estudiantes.append({
                    'estudiante': estudiante,
                    'grado': asignacion.seccion.grado.nombre_grado,
                    'seccion': asignacion.seccion.nombre_seccion,
                    'materia': asignacion.materia.nombre_materia,
                    'id_asignacion': asignacion.id_asignacion
                })
    elif user_role == 1:  # Coordinador
        secciones = Seccion.query.filter_by(id_coordinador=user_id, activo=True).all()
        for seccion in secciones:
            matriculas = Matricula.query.filter_by(id_seccion=seccion.id_seccion, activa=True).all()
            for m in matriculas:
                estudiante = Estudiante.query.get(m.id_estudiante)
                estudiantes.append({
                    'estudiante': estudiante,
                    'grado': seccion.grado.nombre_grado,
                    'seccion': seccion.nombre_seccion,
                    'materia': None,
                    'id_asignacion': None
                })
    return render_template('mis_estudiantes/lista.html', estudiantes=estudiantes)


@mis_estudiantes_bp.route('/ver-boleta/<int:id_estudiante>/<int:id_asignacion>')
def ver_boleta(id_estudiante, id_asignacion):
    """Renderiza la boleta en HTML para previsualizar el formato exacto (no genera PDF)."""
    estudiante = Estudiante.query.get_or_404(id_estudiante)
    matricula = Matricula.query.filter_by(id_estudiante=id_estudiante, activa=True).first()
    if not matricula:
        flash('No se encontró matrícula activa para el estudiante.', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))

    # Determinar asignaciones a mostrar
    if id_asignacion and id_asignacion != 0:
        asignaciones = [MateriaSeccion.query.get_or_404(id_asignacion)]
    else:
        asignaciones = MateriaSeccion.query.filter_by(id_seccion=matricula.id_seccion).all()

    # Si se muestra una sola asignación, exponerla como 'asignacion' para la plantilla (compatibilidad)
    asignacion_obj = asignaciones[0] if len(asignaciones) == 1 else None

    periodos = Periodo.query.filter_by(id_ano_lectivo=matricula.seccion.id_ano_lectivo).order_by(Periodo.numero_periodo).all()

    materias_data = []
    for asig in asignaciones:
        notas_periodos = []
        actitud_periodos = []
        for per in periodos:
            cal = Calificacion.query.filter_by(id_estudiante=id_estudiante, id_asignacion=asig.id_asignacion, id_periodo=per.id_periodo).first()
            if cal:
                pp = PromedioPeriodo.query.filter_by(id_calificacion=cal.id_calificacion).first()
                if pp and getattr(pp, 'nota_prueba_objetiva', None) is not None:
                    # intentar leer nota final de periodo (si existe) o nota_prueba_objetiva
                    if hasattr(pp, 'nota_final_periodo') and getattr(pp, 'nota_final_periodo') is not None:
                        notas_periodos.append(float(pp.nota_final_periodo))
                    else:
                        # usar nota_prueba_objetiva como aproximación
                        notas_periodos.append(float(getattr(pp, 'nota_prueba_objetiva', 0)))
                if pp and getattr(pp, 'nota_actitud', None) is not None:
                    actitud_periodos.append(getattr(pp, 'nota_actitud'))

        trim_notas = notas_periodos[:3]
        trimestre = format(sum(trim_notas)/len(trim_notas), '.1f') if trim_notas else '--'
        examen = format(notas_periodos[-1], '.1f') if len(notas_periodos) > 3 else (format(notas_periodos[-1], '.1f') if notas_periodos else '--')
        actitud = 'MB'
        if actitud_periodos:
            from collections import Counter
            actitud = Counter(actitud_periodos).most_common(1)[0][0]

        materia_info = {
            'nombre_materia': asig.materia.nombre_materia if asig.materia else 'Sin materia',
            'trimestre': trimestre,
            'examen': examen,
            'actitud': actitud,
            'periodo1': format(notas_periodos[0], '.1f') if len(notas_periodos) > 0 else '--',
            'periodo2': format(notas_periodos[1], '.1f') if len(notas_periodos) > 1 else '--',
            'periodo3': format(notas_periodos[2], '.1f') if len(notas_periodos) > 2 else '--',
            'periodo4': format(notas_periodos[3], '.1f') if len(notas_periodos) > 3 else '--',
            'final': format(sum(notas_periodos)/len(notas_periodos), '.1f') if notas_periodos else '--'
        }
        materias_data.append(materia_info)

    notas_finales = [float(m['final']) for m in materias_data if m['final'] != '--']
    promedio_global = format(sum(notas_finales)/len(notas_finales), '.1f') if notas_finales else '--'

    faltas = {'ene': '-', 'feb': '-', 'mar': '-', 'abr': '-', 'may': '-', 'jun': '-', 'jul': '-', 'ago': '-', 'sep': '-', 'oct': '-', 'total': '0'}
    esc_padres = {'p1': 'SI', 'p2': 'SI', 'p3': '-', 'p4': '-'}
    fecha_actual = datetime.datetime.now().strftime('%d/%m/%Y')

    return render_template('mis_estudiantes/boleta.html',
        estudiante=estudiante,
        seccion=matricula.seccion,
        asignacion=asignacion_obj,
        materias=materias_data,
        promedio_global=promedio_global,
        faltas=faltas,
        esc_padres=esc_padres,
        ano_lectivo=matricula.seccion.ano_lectivo,
        fecha_actual=fecha_actual)

@mis_estudiantes_bp.route('/descargar-boleta/<int:id_estudiante>/<int:id_asignacion>')
def descargar_boleta(id_estudiante, id_asignacion):
    # Obtener el estudiante
    estudiante = Estudiante.query.get_or_404(id_estudiante)
    matricula = Matricula.query.filter_by(id_estudiante=id_estudiante, activa=True).first()
    
    if not matricula:
        flash('No se encontró matrícula activa para el estudiante.', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))
    
    # Obtener asignaciones y periodos
    seccion_id = matricula.id_seccion
    asignaciones = MateriaSeccion.query.filter_by(id_seccion=seccion_id).all()
    periodos = Periodo.query.filter_by(id_ano_lectivo=matricula.seccion.id_ano_lectivo).order_by(Periodo.numero_periodo).all()
    
    # Preparar datos para el template
    materias_data = []
    for asig in asignaciones:
        notas_periodos = []
        suma_total = 0
        num_notas = 0
        
        for per in periodos:
            cal = Calificacion.query.filter_by(
                id_estudiante=id_estudiante, 
                id_asignacion=asig.id_asignacion, 
                id_periodo=per.id_periodo
            ).first()
            
            if cal:
                pp = PromedioPeriodo.query.filter_by(id_calificacion=cal.id_calificacion).first()
                if pp and pp.nota_final_periodo is not None:
                    nota = float(pp.nota_final_periodo)
                    notas_periodos.append(nota)
                    suma_total += nota
                    num_notas += 1
            
        materia_info = {
            'nombre_materia': asig.materia.nombre_materia,
            'trimestre': format(sum(notas_periodos[:3])/3, '.1f') if len(notas_periodos) >= 3 else '--',
            'examen': format(notas_periodos[-1], '.1f') if notas_periodos else '--',
            'actitud': 'MB',  # MB = Muy Bueno por defecto
            'periodo1': format(notas_periodos[0], '.1f') if len(notas_periodos) > 0 else '--',
            'periodo2': format(notas_periodos[1], '.1f') if len(notas_periodos) > 1 else '--',
            'periodo3': format(notas_periodos[2], '.1f') if len(notas_periodos) > 2 else '--',
            'periodo4': format(notas_periodos[3], '.1f') if len(notas_periodos) > 3 else '--',
            'final': format(suma_total/num_notas, '.1f') if num_notas > 0 else '--'
        }
        materias_data.append(materia_info)
    # Importar reportlab localmente para evitar error en el arranque si no está instalado
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.units import mm
    except ImportError:
        flash('La librería reportlab no está instalada en este entorno. Instálala con: pip install reportlab', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))
    # Construir lista de materias y promedios para el estudiante (todas las materias de la sección)
    rows = []
    # intentar obtener la matrícula activa para conocer la sección
    matricula = Matricula.query.filter_by(id_estudiante=id_estudiante, activa=True).first()
    if not matricula:
        flash('No se encontró matrícula activa para el estudiante.', 'danger')
        return redirect(url_for('mis_estudiantes.mis_estudiantes'))

    seccion_id = matricula.id_seccion
    asignaciones = MateriaSeccion.query.filter_by(id_seccion=seccion_id).all()
    # obtener periodos del año lectivo de la sección
    periodos = Periodo.query.filter_by(id_ano_lectivo=matricula.seccion.id_ano_lectivo).order_by(Periodo.numero_periodo).all()
    for a in asignaciones:
        materia = a.materia.nombre_materia if a.materia else 'Sin materia'
        # construir notas por periodo
        notas_por_periodo = []
        period_final_values = []
        for per in periodos:
            # buscar calificacion en ese periodo
            cal = Calificacion.query.filter_by(id_estudiante=id_estudiante, id_asignacion=a.id_asignacion, id_periodo=per.id_periodo).first()
            value = ''
            if cal:
                pp = PromedioPeriodo.query.filter_by(id_calificacion=cal.id_calificacion).first()
                if pp and pp.nota_final_periodo is not None:
                    value = float(pp.nota_final_periodo)
                    period_final_values.append(value)
                else:
                    # fallback: promedio simple de las calificaciones en ese periodo/asignacion
                    cal_list = Calificacion.query.filter_by(id_estudiante=id_estudiante, id_asignacion=a.id_asignacion, id_periodo=per.id_periodo).all()
                    if cal_list:
                        s = sum([float(x.nota) for x in cal_list])
                        value = round(s / len(cal_list), 2)
                        period_final_values.append(value)
            notas_por_periodo.append(value)

        # promedio final anual (si hay periodos con valores)
        final_media = ''
        if period_final_values:
            final_media = round(sum(period_final_values) / len(period_final_values), 2)

        rows.append({
            'materia': materia,
            'notas_periodos': notas_por_periodo,
            'final': final_media
        })

    # Generar PDF A4 con estilo parecido a la boleta
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Intentar cargar logo
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.jpg')
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, width-90*mm, height-40*mm, width=50*mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Encabezado grande
    c.setFont('Times-Bold', 22)
    c.setFillColor(colors.HexColor('#0D2C63'))
    c.drawCentredString(width/2, height-25*mm, 'Colegio Santa María')
    c.setFont('Times-Roman', 12)
    c.drawCentredString(width/2, height-32*mm, 'Hijas de Santa María del Corazón de Jesús')

    # Sub-encabezado
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(20*mm, height-38*mm, width-20*mm, height-38*mm)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(20*mm, height-44*mm, 'INFORME DE NOTAS  AÑO ' + str(matricula.seccion.ano_lectivo.ano if matricula.seccion and matricula.seccion.ano_lectivo else ''))

    # Cajón de datos del alumno (rectángulo)
    box_x = 20*mm
    box_y = height-70*mm
    box_w = width-40*mm
    box_h = 20*mm
    c.roundRect(box_x, box_y, box_w, box_h, 3*mm, stroke=1, fill=0)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(box_x+4*mm, box_y+box_h-6*mm, f'ALUMNO/ALUMNA: {estudiante.apellidos.upper()}, {estudiante.nombres.upper()}')
    c.setFont('Helvetica', 9)
    grado_text = ''
    seccion_text = ''
    if matricula.seccion:
        grado_text = matricula.seccion.grado.nombre_grado if matricula.seccion.grado else ''
        seccion_text = matricula.seccion.nombre_seccion
    c.drawString(box_x+4*mm, box_y+4*mm, f'Grado: {grado_text}    Sección: {seccion_text}    Fecha: {datetime.date.today().strftime("%d/%m/%Y")}')

    # Tabla de materias con columnas por periodo + FINAL
    table_x = 20*mm
    table_y = box_y-10*mm
    row_h = 8*mm
    # calcular anchos: columna materia grande, luego N periodos, luego final
    margin = 20*mm
    usable = width - margin*2
    materia_w = 80*mm
    remaining = usable - materia_w
    n_periods = max(1, len(periodos))
    col_w = remaining / (n_periods + 1)  # +1 para columna FINAL

    # Encabezados
    c.setFont('Helvetica-Bold', 9)
    x = table_x
    y = table_y
    # Materia header
    c.rect(x, y-row_h, materia_w, row_h, stroke=1, fill=0)
    c.drawString(x+3*mm, y-6*mm, 'MATERIAS')
    x += materia_w
    # Periodos headers
    for per in periodos:
        c.rect(x, y-row_h, col_w, row_h, stroke=1, fill=0)
        c.drawCentredString(x+col_w/2, y-6*mm, per.nombre_periodo)
        x += col_w
    # Final header
    c.rect(x, y-row_h, col_w, row_h, stroke=1, fill=0)
    c.drawCentredString(x+col_w/2, y-6*mm, 'FINAL')

    # Filas
    c.setFont('Helvetica', 9)
    y -= row_h
    for r in rows:
        x = table_x
        # materia
        c.rect(x, y-row_h, materia_w, row_h, stroke=1, fill=0)
        c.drawString(x+3*mm, y-6*mm, str(r['materia'])[:70])
        x += materia_w
        # periodos
        notas = r.get('notas_periodos', [])
        for i in range(n_periods):
            val = notas[i] if i < len(notas) else ''
            c.rect(x, y-row_h, col_w, row_h, stroke=1, fill=0)
            c.drawCentredString(x+col_w/2, y-6*mm, str(val))
            x += col_w
        # final
        c.rect(x, y-row_h, col_w, row_h, stroke=1, fill=0)
        c.drawCentredString(x+col_w/2, y-6*mm, str(r.get('final', '')))

        y -= row_h
        if y < 40*mm:
            c.showPage()
            y = height-30*mm

    # Nota minima y observaciones
    c.setFont('Helvetica-Oblique', 8)
    c.drawString(table_x, y-6*mm, '* LA NOTA MÍNIMA DEL COLEGIO ES 7.0')

    # Pie con datos de contacto
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, 15*mm, 'Av. Independencia Sur y 37 Calle Oriente, Barrio Nuevo, Santa Ana, El Salvador')
    c.drawString(20*mm, 10*mm, 'Email: colegiosantamaria@hotmail.es   Tel.: 2440-1490   www.hscmj.org')

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, download_name=f'boleta_{estudiante.nie}.pdf', mimetype='application/pdf')
