from flask import redirect, url_for, flash
# Gestión de criterios de evaluación integral
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
	# Obtener ámbitos y apartados
	ambitos = EvaluacionIntegralAmbito.query.order_by(EvaluacionIntegralAmbito.orden).all()
	apartados = EvaluacionIntegralApartado.query.order_by(EvaluacionIntegralApartado.orden).all()

	# Filtros seleccionados
	if request.method == 'POST':
		id_periodo = request.form.get('id_periodo', type=int)
		id_ambito = request.form.get('id_ambito', type=int)
		id_apartado = request.form.get('id_apartado', type=int)
	else:
		id_periodo = request.args.get('id_periodo', type=int) or (periodos[0].id_periodo if periodos else None)
		id_ambito = request.args.get('id_ambito', type=int)
		id_apartado = request.args.get('id_apartado', type=int)

	# Filtrar criterios por grado y apartado seleccionado
	criterios = []
	if id_apartado:
		criterios = EvaluacionIntegralCriterio.query.filter_by(id_grado=id_grado, id_apartado=id_apartado).order_by(EvaluacionIntegralCriterio.orden).all()

	from flask import session
	if request.method == 'POST' and 'valoracion_{}_{}`'.format(criterios[0].id_criterio if criterios else '', estudiantes[0].id_estudiante if estudiantes else '') in request.form:
		id_maestro = session.get('user_id')
		# Guardar valoraciones para todos los estudiantes y criterios
		for estudiante in estudiantes:
			for criterio in criterios:
				valor = request.form.get(f"valoracion_{criterio.id_criterio}_{estudiante.id_estudiante}")
				if valor:
					resultado = EvaluacionIntegralResultado.query.filter_by(
						id_estudiante=estudiante.id_estudiante,
						id_criterio=criterio.id_criterio,
						id_periodo=id_periodo
					).first()
					if resultado:
						resultado.valoracion = valor
						resultado.id_maestro = id_maestro
					else:
						resultado = EvaluacionIntegralResultado(
							id_estudiante=estudiante.id_estudiante,
							id_criterio=criterio.id_criterio,
							id_periodo=id_periodo,
							valoracion=valor,
							id_maestro=id_maestro
						)
						db.session.add(resultado)
		db.session.commit()
		flash('Valoraciones guardadas correctamente.', 'success')

	# Obtener valoraciones existentes para mostrar en la UI
	valoraciones = {}
	if id_periodo and criterios:
		resultados = EvaluacionIntegralResultado.query.filter(
			EvaluacionIntegralResultado.id_periodo == id_periodo,
			EvaluacionIntegralResultado.id_criterio.in_([c.id_criterio for c in criterios]),
			EvaluacionIntegralResultado.id_estudiante.in_([e.id_estudiante for e in estudiantes])
		).all()
		for r in resultados:
			valoraciones[(r.id_criterio, r.id_estudiante)] = r.valoracion
	return render_template('evaluacion_integral/ingreso.html', estudiantes=estudiantes, periodos=periodos, ambitos=ambitos, apartados=apartados, criterios=criterios, id_periodo=id_periodo, id_ambito=id_ambito, id_apartado=id_apartado, valoraciones=valoraciones)

@evaluacion_integral_bp.route('/criterios', methods=['GET', 'POST'])
def gestionar_criterios():
	from models.Grados import Grado
	from models.EvaluacionIntegralAmbito import EvaluacionIntegralAmbito
	from models.EvaluacionIntegralApartado import EvaluacionIntegralApartado
	from models.EvaluacionIntegralCriterio import EvaluacionIntegralCriterio
	# Obtener grados, ámbitos y apartados
	grados = Grado.query.order_by(Grado.nombre_grado).all()
	ambitos = EvaluacionIntegralAmbito.query.order_by(EvaluacionIntegralAmbito.orden).all()
	apartados = EvaluacionIntegralApartado.query.order_by(EvaluacionIntegralApartado.orden).all()

	# Filtros seleccionados
	if request.method == 'POST':
		id_grado = request.form.get('id_grado', type=int)
		id_ambito = request.form.get('id_ambito', type=int)
		id_apartado = request.form.get('id_apartado', type=int)
	else:
		id_grado = request.args.get('id_grado', type=int)
		id_ambito = request.args.get('id_ambito', type=int)
		id_apartado = request.args.get('id_apartado', type=int)
	criterios = []
	if id_grado and id_apartado:
		criterios = EvaluacionIntegralCriterio.query.filter_by(id_grado=id_grado, id_apartado=id_apartado).order_by(EvaluacionIntegralCriterio.orden).all()

	# Agregar criterio
	if request.method == 'POST' and request.args.get('add') == '1':
		descripcion = request.form.get('descripcion_criterio', '').strip()
		id_apartado_post = int(request.form.get('id_apartado'))
		id_grado_post = int(request.form.get('id_grado'))
		count_criterios = EvaluacionIntegralCriterio.query.filter_by(id_apartado=id_apartado_post, id_grado=id_grado_post).count()
		if descripcion and count_criterios < 10:
			nuevo_criterio = EvaluacionIntegralCriterio(
				id_apartado=id_apartado_post,
				id_grado=id_grado_post,
				descripcion=descripcion,
				orden=count_criterios+1
			)
			db.session.add(nuevo_criterio)
			db.session.commit()
			flash('Criterio agregado correctamente.', 'success')
			return redirect(url_for('evaluacion_integral_bp.gestionar_criterios', id_grado=id_grado_post, id_apartado=id_apartado_post))
		else:
			flash('No se puede agregar más de 10 criterios o la descripción está vacía.', 'danger')
			return redirect(request.url)

	# Editar criterio
	if request.method == 'POST' and request.args.get('edit'):
		id_criterio = int(request.args.get('edit'))
		descripcion = request.form.get('descripcion_criterio', '').strip()
		criterio = EvaluacionIntegralCriterio.query.get(id_criterio)
		if criterio and descripcion:
			criterio.descripcion = descripcion
			db.session.commit()
			flash('Criterio editado correctamente.', 'success')
			return redirect(url_for('evaluacion_integral_bp.gestionar_criterios', id_grado=criterio.id_grado, id_apartado=criterio.id_apartado))
		else:
			flash('No se pudo editar el criterio.', 'danger')
			return redirect(request.url)

	# Eliminar criterio
	if request.method == 'POST' and request.args.get('delete'):
		id_criterio = int(request.args.get('delete'))
		criterio = EvaluacionIntegralCriterio.query.get(id_criterio)
		if criterio:
			id_grado_del = criterio.id_grado
			id_apartado_del = criterio.id_apartado
			db.session.delete(criterio)
			db.session.commit()
			flash('Criterio eliminado correctamente.', 'success')
			return redirect(url_for('evaluacion_integral_bp.gestionar_criterios', id_grado=id_grado_del, id_apartado=id_apartado_del))
		else:
			flash('No se pudo eliminar el criterio.', 'danger')
			return redirect(request.url)

	return render_template('evaluacion_integral/criterios.html', grados=grados, ambitos=ambitos, apartados=apartados, criterios=criterios, id_grado=id_grado, id_ambito=id_ambito, id_apartado=id_apartado)
