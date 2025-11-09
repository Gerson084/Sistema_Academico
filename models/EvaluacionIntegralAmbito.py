from db import db

class EvaluacionIntegralAmbito(db.Model):
    __tablename__ = 'evaluacion_integral_ambitos'
    id_ambito = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    orden = db.Column(db.Integer, default=0)
    apartados = db.relationship('EvaluacionIntegralApartado', backref='ambito', cascade='all, delete-orphan')
