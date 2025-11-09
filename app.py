from flask import Flask, jsonify, render_template, redirect, url_for
from db import DatabaseConfig, test_connection
from appEstudiantes import estudiantes_bp

from routes.user_route import users
#from routes.rol_route import rol
from models import Estudiantes
from routes.appSecciones import secciones_bp
from dotenv import load_dotenv
from routes.auth_route import auth_bp
from routes.rol_route import rol
from routes.change_password_route import change_password_bp
from routes.recover_route import recover_bp
from routes.matricula_route import matriculas_bp
from routes.appGrados import grados_bp
from routes.appMaterias import materias_bp

from routes.materia_seccion_route import materia_seccion_bp
from routes.notas_route import notas_bp
from routes.docente_notas_route import docente_notas_bp
from routes.coordinador_route import coordinador_bp

from routes.reportesC_bp import reportesC_bp
from routes.mis_estudiantes_bp import mis_estudiantes_bp

from routes.inasistencias_bp import inasistencias_bp
from routes.incidentes_bp import incidentes_bp
from routes.conducta_grado_route import conducta_grado_bp
from routes.evaluacion_integral_bp import evaluacion_integral_bp



import os
# Cargar variables de entorno desde .env
load_dotenv()


app = Flask(__name__)

# Configuración de Flask-Mail (opcional)
try:
    from flask_mail import Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    mail = Mail(app)
except Exception:
    # flask_mail no está instalado o hay error en la configuración; continuar sin Mail
    mail = None

# Configurar secret key para sesiones y flash
app.secret_key = os.getenv("SECRET_KEY")  # <--- esto es crucial

# Inicializar la DB
db = DatabaseConfig.init_app(app)

# Registrar blueprint
app.register_blueprint(estudiantes_bp, url_prefix="/estudiantes")
app.register_blueprint(users)
app.register_blueprint(rol)
app.register_blueprint(secciones_bp, url_prefix="/secciones")
#app.register_blueprint(rol)

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(change_password_bp, url_prefix="/auth")
app.register_blueprint(recover_bp, url_prefix="/auth")
app.register_blueprint(matriculas_bp, url_prefix="/matriculas")
app.register_blueprint(grados_bp, url_prefix='/grados')
app.register_blueprint(materias_bp, url_prefix='/materias')

app.register_blueprint(materia_seccion_bp, url_prefix='/asignaciones')
app.register_blueprint(notas_bp)
app.register_blueprint(docente_notas_bp, url_prefix='/docente')
app.register_blueprint(coordinador_bp, url_prefix='/coordinador')

app.register_blueprint(reportesC_bp, url_prefix='/reportesC')
app.register_blueprint(mis_estudiantes_bp)
app.register_blueprint(inasistencias_bp)

app.register_blueprint(incidentes_bp)
app.register_blueprint(conducta_grado_bp)
app.register_blueprint(evaluacion_integral_bp)

# Rutas de compatibilidad: redirigen a los endpoints del blueprint con prefijo
@app.route('/reporte_conducta_estudiante')
def redirect_reporte_conducta_estudiante():
    return redirect(url_for('reportes.reporte_conducta_estudiante'))


@app.route('/reporte_conducta_periodo')
def redirect_reporte_conducta_periodo():
    return redirect(url_for('reportes.reporte_conducta_periodo'))








@app.route('/')
def home():
    return render_template('auth/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard principal para administradores"""
    return render_template('dashboards/admin_dashboard.html')


@app.route('/test-db')
def test_db():
    """Ruta para probar la conexión a la base de datos"""
    result = test_connection()
    if result['status'] == 'error':
        return jsonify(result), 500
    return jsonify(result)


@app.route('/_routes')
def show_routes():
    """Ruteo de depuración: lista todas las rutas registradas (solo para desarrollo)."""
    output = []
    for rule in app.url_map.iter_rules():
        output.append(f"{rule.endpoint}: {rule}")
    return '<br>'.join(output)

if __name__ == '__main__':
    with app.app_context():
        # Reflejar la base de datos nuevamente
        db.reflect()

        # Mostrar todas las tablas detectadas
        print("Tablas disponibles:", db.metadata.tables.keys())

        # Mostrar columnas de la tabla 'estudiantes'
        if 'estudiantes' in db.metadata.tables:
            estudiantes_table = db.metadata.tables['estudiantes']
            print("Columnas de 'estudiantes':", [col.name for col in estudiantes_table.columns])
        else:
            print("❌ La tabla 'estudiantes' no se encuentra en la base de datos")

        # Asegurarse de que SQLAlchemy vea los modelos
        db.create_all()
        # Probar conexión y ver tablas
        print(test_connection())
    app.run(debug=True)
