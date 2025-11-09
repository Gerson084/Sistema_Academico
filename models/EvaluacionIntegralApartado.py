from db import db

class EvaluacionIntegralApartado(db.Model):
    __tablename__ = 'evaluacion_integral_apartados'
    id_apartado = db.Column(db.Integer, primary_key=True)
    id_ambito = db.Column(db.Integer, db.ForeignKey('evaluacion_integral_ambitos.id_ambito'), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    orden = db.Column(db.Integer, default=0)
    criterios = db.relationship('EvaluacionIntegralCriterio', backref='apartado', cascade='all, delete-orphan')
