"""
Paquete de configuración de base de datos para el Sistema Académico
"""

from .cn import db, DatabaseConfig, get_db, test_connection

__all__ = ['db', 'DatabaseConfig', 'get_db', 'test_connection']