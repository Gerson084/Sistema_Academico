# models/AnosLectivos.py
from db import db

class AnoLectivo(db.Model):
    __tablename__ = 'anos_lectivos'

    id_ano_lectivo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ano = db.Column(db.Integer, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, default=True)
