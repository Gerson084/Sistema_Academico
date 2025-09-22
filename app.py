from flask import Flask, jsonify, render_template
from db import DatabaseConfig, test_connection
from appEstudiantes import estudiantes_bp
from models import Estudiante
from routes.user_route import users

app = Flask(__name__)

# Inicializar la DB
db = DatabaseConfig.init_app(app)

# Registrar blueprint
app.register_blueprint(estudiantes_bp, url_prefix="/estudiantes")

@app.route('/')
def home():
    return render_template('base.html')


app.register_blueprint(users)

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
