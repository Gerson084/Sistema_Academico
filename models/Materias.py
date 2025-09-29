# models/Materias.py
from db import db

class Materia(db.Model):
    __tablename__ = "materias"

    id_materia = db.Column(db.Integer, primary_key=True)
    nombre_materia = db.Column(db.String(100), nullable=False)
    codigo_materia = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    activa = db.Column(db.Boolean, default=True)
