from db import db
from datetime import datetime
from sqlalchemy import Enum

class Estudiante(db.Model):
    """Modelo para representar un estudiante en el sistema académico"""
    
    __tablename__ = 'estudiantes'
    
    # Campos de la tabla
    id_estudiante = db.Column(db.Integer, primary_key=True)
    nie = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    genero = db.Column(Enum('M','F', name='genero_enum'), nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    nombre_padre = db.Column(db.String(100), nullable=True)
    nombre_madre = db.Column(db.String(100), nullable=True)
    telefono_emergencia = db.Column(db.String(20), nullable=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
   
    
    def __repr__(self):
        return f'<Estudiante {self.nie}: {self.nombres} {self.apellidos}>'
    
    def to_dict(self):
        """Convertir el modelo a diccionario para JSON"""
        return {
            'id_estudiante': self.id_estudiante,
            'nie': self.nie,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'genero': self.genero,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'nombre_padre': self.nombre_padre,
            'nombre_madre': self.nombre_madre,
            'telefono_emergencia': self.telefono_emergencia,
            'activo': self.activo,
            'fecha_ingreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            
        }
    
    @staticmethod
    def crear_estudiante(nie, nombres, apellidos, **kwargs):
        """Método estático para crear un nuevo estudiante"""
        nuevo_estudiante = Estudiante(
            nie=nie,
            nombres=nombres,
            apellidos=apellidos,
            **kwargs
        )
        db.session.add(nuevo_estudiante)
        db.session.commit()
        return nuevo_estudiante
    
    def actualizar(self, **kwargs):
        """Actualizar los datos del estudiante"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
    
    def eliminar(self):
        """Eliminar estudiante (soft delete)"""
        self.activo = False
        self.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
    
    def restaurar(self):
        """Restaurar estudiante eliminado"""
        self.activo = True
        self.fecha_actualizacion = datetime.utcnow()
        db.session.commit()
