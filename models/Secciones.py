# db/models/seccion.py
from db import db

class Seccion(db.Model):
    __tablename__ = 'secciones'
    id_seccion = db.Column(db.Integer, primary_key=True)
    id_grado = db.Column(db.Integer, db.ForeignKey('grados.id_grado'), nullable=False)
    nombre_seccion = db.Column(db.String(10), nullable=False)
    id_ano_lectivo = db.Column(db.Integer, db.ForeignKey('anos_lectivos.id_ano_lectivo'), nullable=False)
    activo = db.Column(db.Boolean, default=True)  
