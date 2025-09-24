from db import db

class Seccion(db.Model):
    __tablename__ = 'secciones'

    id_seccion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_grado = db.Column(db.Integer, nullable=False)
    nombre_seccion = db.Column(db.String(10), nullable=False)
    id_ano_lectivo = db.Column(db.Integer, nullable=False)
