from flask import Blueprint

evaluacion_integral_bp = Blueprint('evaluacion_integral_bp', __name__, url_prefix='/evaluacion-integral')


# Ruta base para ingreso de evaluación integral
from flask import render_template, request
from models.Secciones import Seccion
from models.Grados import Grado
from models.AnosLectivos import AnoLectivo
from models.EvaluacionIntegralAmbito import EvaluacionIntegralAmbito
from models.EvaluacionIntegralApartado import EvaluacionIntegralApartado
from models.EvaluacionIntegralCriterio import EvaluacionIntegralCriterio
from models.EvaluacionIntegralResultado import EvaluacionIntegralResultado
from models.Estudiantes import Estudiante
from models.matriculas import Matricula
from models.Periodos import Periodo
from db import db

@evaluacion_integral_bp.route('/ingreso/<int:id_seccion>/<int:id_grado>/<int:id_ano_lectivo>', methods=['GET', 'POST'])
def ingreso(id_seccion, id_grado, id_ano_lectivo):
	from flask import redirect, url_for, flash
	# Obtener estudiantes activos en la sección
	estudiantes = db.session.query(Estudiante).join(Matricula).filter(
		Matricula.id_seccion == id_seccion,
		Matricula.activa == True,
		Estudiante.activo == True
	).order_by(Estudiante.apellidos, Estudiante.nombres).all()
	# Obtener periodos del año lectivo
	periodos = Periodo.query.filter_by(id_ano_lectivo=id_ano_lectivo).order_by(Periodo.numero_periodo).all()
	# Obtener ámbitos, apartados y criterios para el grado
	ambitos = EvaluacionIntegralAmbito.query.order_by(EvaluacionIntegralAmbito.orden).all()
	apartados = EvaluacionIntegralApartado.query.order_by(EvaluacionIntegralApartado.orden).all()
	criterios = EvaluacionIntegralCriterio.query.filter_by(id_grado=id_grado).order_by(EvaluacionIntegralCriterio.orden).all()

	from flask import session
	if request.method == 'POST':
		# Agregar nuevo criterio
		if 'descripcion_criterio' in request.form and 'id_apartado' in request.form:
			descripcion = request.form['descripcion_criterio'].strip()
			id_apartado = int(request.form['id_apartado'])
			# Validar máximo 10 criterios por apartado y grado
			count_criterios = EvaluacionIntegralCriterio.query.filter_by(id_apartado=id_apartado, id_grado=id_grado).count()
			if count_criterios < 10 and descripcion:
				nuevo_criterio = EvaluacionIntegralCriterio(
					id_apartado=id_apartado,
					id_grado=id_grado,
					descripcion=descripcion,
					orden=count_criterios+1
				)
				db.session.add(nuevo_criterio)
				db.session.commit()
				flash('Criterio agregado correctamente.', 'success')
			else:
				flash('No se puede agregar más de 10 criterios o la descripción está vacía.', 'danger')
			return redirect(request.url)

		# Guardar valoraciones SOLO del estudiante enviado
		id_periodo = int(request.form.get('id_periodo'))
		id_maestro = session.get('user_id')
		id_estudiante = int(request.form.get('id_estudiante'))
		for criterio in criterios:
			valor = request.form.get(f"valoracion_{criterio.id_criterio}")
			if valor:
				resultado = EvaluacionIntegralResultado.query.filter_by(
					id_estudiante=id_estudiante,
					id_criterio=criterio.id_criterio,
					id_periodo=id_periodo
				).first()
				if resultado:
					resultado.valoracion = valor
					resultado.id_maestro = id_maestro
				else:
					resultado = EvaluacionIntegralResultado(
						id_estudiante=id_estudiante,
						id_criterio=criterio.id_criterio,
						id_periodo=id_periodo,
						valoracion=valor,
						id_maestro=id_maestro
					)
					db.session.add(resultado)
		db.session.commit()
		flash('Valoraciones guardadas correctamente.', 'success')
		return redirect(request.url)

	# Obtener valoraciones existentes para mostrar en la UI
	id_periodo = request.args.get('id_periodo', type=int) or (periodos[0].id_periodo if periodos else None)
	valoraciones = {}
	if id_periodo:
		resultados = EvaluacionIntegralResultado.query.filter(
			EvaluacionIntegralResultado.id_periodo == id_periodo,
			EvaluacionIntegralResultado.id_criterio.in_([c.id_criterio for c in criterios]),
			EvaluacionIntegralResultado.id_estudiante.in_([e.id_estudiante for e in estudiantes])
		).all()
		for r in resultados:
			valoraciones[(r.id_criterio, r.id_estudiante)] = r.valoracion
	return render_template('evaluacion_integral/ingreso.html', estudiantes=estudiantes, periodos=periodos, ambitos=ambitos, apartados=apartados, criterios=criterios, id_periodo=id_periodo, valoraciones=valoraciones)
