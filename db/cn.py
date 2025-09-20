from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import pymysql
from flask import Flask

# Instalar PyMySQL como driver
pymysql.install_as_MySQLdb()

# Inicializar SQLAlchemy
db = SQLAlchemy()

class DatabaseConfig:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:KdavjHoyqdUFDRgtjZcYkoPcHrTazCgI@tramway.proxy.rlwy.net:35552/sistema_academico"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app: Flask):
        app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConfig.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS

        db.init_app(app)

        # Reflejar tablas y asegurar que se vean
        with app.app_context():
            db.reflect()
            print("Tablas disponibles:", db.metadata.tables.keys())

        return db

def get_db():
    """Función para obtener la instancia de la base de datos"""
    return db

def test_connection():
    """Función para probar la conexión a la base de datos"""
    try:
        # Usar text() para consultas SQL directas en SQLAlchemy 2.0+
        result = db.session.execute(text('SELECT DATABASE()')).fetchone()
        db.session.commit()
        return {
            'status': 'success',
            'message': 'Conexión a la base de datos exitosa',
            'database': result[0] if result else 'railway'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error al conectar con la base de datos: {str(e)}'
        }
