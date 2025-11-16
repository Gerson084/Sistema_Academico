from flask import Blueprint, render_template, request, redirect, url_for, session
from models.Estudiantes import Estudiante
from models.Grados import Grado
from models.Secciones import Seccion
from models.Materias import Materia
from models.MateriaSeccion import MateriaSeccion
from models.Periodos import Periodo
from models.AnosLectivos import AnoLectivo
from db import db
from sqlalchemy import text

admin_notas_bp = Blueprint('admin_notas', __name__, template_folder='templates')

@admin_notas_bp.route('/admin/notas-finales')
def admin_notas_finales():
    """Vista administrativa para consultar notas finales de cualquier asignación"""
    # Verificar que sea administrador
    if session.get('user_role') != 1:
        return redirect(url_for('auth.login'))
    
    # Obtener filtros
    id_ano_lectivo = request.args.get('ano_lectivo', type=int)
    id_seccion = request.args.get('seccion', type=int)
    id_asignacion = request.args.get('asignacion', type=int)
    
    # DEBUG
    print(f"\n=== ADMIN NOTAS FINALES ===")
    print(f"Parámetros recibidos: ano={id_ano_lectivo}, seccion={id_seccion}, asignacion={id_asignacion}")
    
    # Obtener todos los años lectivos
    anos_lectivos = AnoLectivo.query.order_by(AnoLectivo.ano.desc()).all()
    print(f"Años lectivos encontrados: {len(anos_lectivos)}")
    
    # Si no se selecciona año, usar el activo
    if not id_ano_lectivo and anos_lectivos:
        ano_activo = AnoLectivo.query.filter_by(activo=1).first()
        if ano_activo:
            id_ano_lectivo = ano_activo.id_ano_lectivo
            print(f"Usando año activo: {id_ano_lectivo}")
    
    # Obtener secciones del año lectivo seleccionado
    secciones = []
    if id_ano_lectivo:
        secciones = Seccion.query.filter_by(
            id_ano_lectivo=id_ano_lectivo
        ).join(Grado).order_by(Grado.orden, Seccion.nombre_seccion).all()
    
    print(f"Secciones encontradas: {len(secciones)}")
    
    # Obtener asignaciones según filtros
    asignaciones = []
    if id_seccion:
        print(f"Buscando asignaciones para sección: {id_seccion}")
        query_asignaciones = text("""
            SELECT 
                ms.id_asignacion,
                m.nombre_materia,
                m.codigo_materia,
                CONCAT(u.nombres, ' ', u.apellidos) as nombre_docente
            FROM materia_seccion ms
            INNER JOIN materias m ON ms.id_materia = m.id_materia
            LEFT JOIN usuarios u ON ms.id_maestro = u.id_usuario
            WHERE ms.id_seccion = :id_seccion
            ORDER BY m.nombre_materia
        """)
        
        result = db.session.execute(query_asignaciones, {'id_seccion': id_seccion})
        asignaciones = [dict(row._mapping) for row in result]
        print(f"Query asignaciones ejecutada para seccion {id_seccion}")
        for asig in asignaciones:
            print(f"  - {asig['nombre_materia']} (ID: {asig['id_asignacion']})")
    
    print(f"Asignaciones encontradas: {len(asignaciones)}")
    
    # Si se seleccionó una asignación, mostrar las notas finales
    estudiantes = []
    info_asignacion = None
    periodos = []
    
    if id_asignacion:
        # Obtener información de la asignación
        query_info = text("""
            SELECT 
                m.nombre_materia,
                m.codigo_materia,
                g.nombre_grado,
                g.nivel,
                s.nombre_seccion,
                al.ano as ano_lectivo,
                al.id_ano_lectivo,
                CONCAT(u.nombres, ' ', u.apellidos) as nombre_docente
            FROM materia_seccion ms
            INNER JOIN materias m ON ms.id_materia = m.id_materia
            INNER JOIN secciones s ON ms.id_seccion = s.id_seccion
            INNER JOIN grados g ON s.id_grado = g.id_grado
            INNER JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
            LEFT JOIN usuarios u ON ms.id_maestro = u.id_usuario
            WHERE ms.id_asignacion = :id_asignacion
        """)
        
        info_result = db.session.execute(query_info, {'id_asignacion': id_asignacion}).first()
        
        if info_result:
            info_asignacion = {
                'nombre_materia': info_result.nombre_materia,
                'codigo_materia': info_result.codigo_materia,
                'grado': f"{info_result.nombre_grado} - {info_result.nivel}",
                'seccion': info_result.nombre_seccion,
                'ano_lectivo': info_result.ano_lectivo,
                'docente': info_result.nombre_docente or 'Sin asignar'
            }
            
            # Periodos del año lectivo
            periodos = Periodo.query.filter_by(
                id_ano_lectivo=info_result.id_ano_lectivo
            ).order_by(Periodo.numero_periodo).all()
            
            # Obtener estudiantes de la sección (sin filtro activa, pero verificando año lectivo)
            asignacion_obj = MateriaSeccion.query.get(id_asignacion)
            if asignacion_obj:
                query_estudiantes = text("""
                    SELECT 
                        e.id_estudiante,
                        e.nie,
                        e.nombres,
                        e.apellidos,
                        mat.id_matricula
                    FROM estudiantes e
                    INNER JOIN matriculas mat ON e.id_estudiante = mat.id_estudiante
                    INNER JOIN secciones s ON mat.id_seccion = s.id_seccion
                    WHERE mat.id_seccion = :id_seccion
                    AND s.id_ano_lectivo = :id_ano_lectivo
                    AND e.activo = 1
                    ORDER BY e.apellidos, e.nombres
                """)
                
                estudiantes_result = db.session.execute(query_estudiantes, {
                    'id_seccion': asignacion_obj.id_seccion,
                    'id_ano_lectivo': info_result.id_ano_lectivo
                })
                
                print(f"Consultando estudiantes: seccion={asignacion_obj.id_seccion}, ano_lectivo={info_result.id_ano_lectivo}")
                
                # Cargar todos los resúmenes de notas para esta asignación
                notas_map = {}
                periodo_ids = [p.id_periodo for p in periodos]
                if periodo_ids:
                    query_resumen = text("""
                        SELECT id_estudiante, id_periodo, nota_final_periodo
                        FROM notas_resumen_periodo
                        WHERE id_asignacion = :id_asignacion
                    """)
                    resumen_result = db.session.execute(query_resumen, {
                        'id_asignacion': id_asignacion
                    })
                    for r in resumen_result:
                        if r.id_periodo in periodo_ids:
                            notas_map[(r.id_estudiante, r.id_periodo)] = float(r.nota_final_periodo) if r.nota_final_periodo is not None else None
                
                # Cargar conducta por período
                conducta_map = {}
                if periodo_ids:
                    query_conducta = text("""
                        SELECT id_estudiante, id_periodo, nota_conducta, conducta_literal
                        FROM conducta_materia_periodo
                        WHERE id_asignacion = :id_asignacion
                    """)
                    conducta_result = db.session.execute(query_conducta, {
                        'id_asignacion': id_asignacion
                    })
                    for c in conducta_result:
                        if c.id_periodo in periodo_ids:
                            conducta_valor = c.conducta_literal if c.conducta_literal else (
                                float(c.nota_conducta) if c.nota_conducta is not None else None
                            )
                            conducta_map[(c.id_estudiante, c.id_periodo)] = conducta_valor
                
                estudiantes = []
                for row in estudiantes_result:
                    id_est = row.id_estudiante
                    notas_por_periodo = []
                    conductas_por_periodo = []
                    valores = []
                    
                    for p in periodos:
                        nota = notas_map.get((id_est, p.id_periodo))
                        conducta = conducta_map.get((id_est, p.id_periodo))
                        notas_por_periodo.append(nota)
                        conductas_por_periodo.append(conducta)
                        if nota is not None:
                            valores.append(nota)
                    
                    promedio_anual = None
                    if valores:
                        promedio_anual = round(sum(valores) / len(valores), 2)
                    
                    estudiantes.append({
                        'id_estudiante': id_est,
                        'nie': row.nie,
                        'nombre_completo': f"{row.apellidos}, {row.nombres}",
                        'id_matricula': row.id_matricula,
                        'notas_por_periodo': notas_por_periodo,
                        'conductas_por_periodo': conductas_por_periodo,
                        'promedio_anual': promedio_anual
                    })
    
    print(f"Total estudiantes procesados: {len(estudiantes)}")
    print(f"=========================\n")
    
    return render_template('admin/admin_notas_finales.html',
                         anos_lectivos=anos_lectivos,
                         secciones=secciones,
                         asignaciones=asignaciones,
                         estudiantes=estudiantes,
                         periodos=periodos,
                         info_asignacion=info_asignacion,
                         id_ano_lectivo=id_ano_lectivo,
                         id_seccion=id_seccion,
                         id_asignacion=id_asignacion)
