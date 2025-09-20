from flask import Flask, jsonify
from db import DatabaseConfig, get_db, test_connection

app = Flask(__name__)

# Configurar la base de datos usando la clase DatabaseConfig
db = DatabaseConfig.init_app(app)

@app.route('/')
def home():
    return "¡Hola, Flask en VS Code!"

@app.route('/test-db')
def test_db():
    """Ruta para probar la conexión a la base de datos"""
    result = test_connection()
    if result['status'] == 'error':
        return jsonify(result), 500
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        # Crear tablas si no existen (opcional)
        db.create_all()
    app.run(debug=True)
