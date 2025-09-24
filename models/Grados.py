# models/Grados.py
from db import db

class Grado(db.Model):
    __tablename__ = 'grados'

    id_grado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_grado = db.Column(db.String(20), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)
