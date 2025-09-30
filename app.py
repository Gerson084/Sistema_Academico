from flask import Flask, jsonify, render_template
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
from routes.matricula_route import matriculas_bp
from routes.appGrados import grados_bp
from routes.appMaterias import materias_bp


import os

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

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
app.register_blueprint(matriculas_bp, url_prefix="/matriculas")
app.register_blueprint(grados_bp, url_prefix='/grados')
app.register_blueprint(materias_bp, url_prefix='/materias')







@app.route('/')
def home():
    return render_template('home.html')



@app.route('/test-db')
def test_db():
    """Ruta para probar la conexión a la base de datos"""
    result = test_connection()
    if result['status'] == 'error':
        return jsonify(result), 500
    return jsonify(result)

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
