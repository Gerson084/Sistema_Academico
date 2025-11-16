# models/Grados.py
from db import db

class Grado(db.Model):
    __tablename__ = "grados"

    id_grado = db.Column(db.Integer, primary_key=True)
    nombre_grado = db.Column(db.String(50), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)  # Orden de progresión educativa
    activo = db.Column(db.Boolean, default=True)  # Para activar/desactivar