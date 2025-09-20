from flask_sqlalchemy import SQLAlchemy
import pymysql
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Instalar PyMySQL como MySQL driver
pymysql.install_as_MySQLdb()

# Inicializar SQLAlchemy
db = SQLAlchemy()

class DatabaseConfig:
    """Clase para manejar la configuración de la base de datos"""
    
    # Configuración de la base de datos usando variables de entorno
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'test')
    
    # Construir URL de conexión
    SQLALCHEMY_DATABASE_URI = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        """Inicializar la configuración de la base de datos en la aplicación Flask"""
        app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConfig.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
        
        # Inicializar SQLAlchemy con la aplicación
        db.init_app(app)
        
        return db

def get_db():
    """Función para obtener la instancia de la base de datos"""
    return db

def test_connection():
    """Función para probar la conexión a la base de datos"""
    try:
        db.session.execute('SELECT 1')
        db.session.commit()
        return {
            'status': 'success',
            'message': 'Conexión a la base de datos exitosa',
            'database': 'railway (MySQL)'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error al conectar con la base de datos: {str(e)}'
        }