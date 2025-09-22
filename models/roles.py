from db import db

class Roles(db.Model):
    __tablename__ = 'roles'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))

    def __init__(self, nombre, descripcion):
        self.nombre = nombre
        self.descripcion = descripcion

