# models/MateriaSeccion.py
from db import db

class MateriaSeccion(db.Model):
    __tablename__ = 'materia_seccion'
    
    id_asignacion = db.Column(db.Integer, primary_key=True)
    id_materia = db.Column(db.Integer, db.ForeignKey('materias.id_materia'), nullable=False)
    id_seccion = db.Column(db.Integer, db.ForeignKey('secciones.id_seccion'), nullable=False)
    id_maestro = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    
    # Relaciones
    materia = db.relationship('Materia', backref='asignaciones')
    seccion = db.relationship('Seccion', backref='asignaciones')
    maestro = db.relationship('Usuario', backref='asignaciones')