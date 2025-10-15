from db import db
from sqlalchemy import Enum

class Rol(db.Model):
    __tablename__ = 'roles'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    estado = db.Column(Enum('Activo', 'Inactivo', name='estado_enum'), nullable=False, default='Activo')

    def __repr__(self):
        return f"<Rol {self.nombre_rol}>"
