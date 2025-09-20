from db import db
from datetime import datetime

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id_estudiante = db.Column(db.Integer, primary_key=True)
    nie = db.Column(db.String(20))
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    genero = db.Column(db.String(10))
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(100))
    nombre_padre = db.Column(db.String(100))
    nombre_madre = db.Column(db.String(100))
    telefono_emergencia = db.Column(db.String(15))
    activo = db.Column(db.Boolean, default=True)
    fecha_ingreso = db.Column(db.Date)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
