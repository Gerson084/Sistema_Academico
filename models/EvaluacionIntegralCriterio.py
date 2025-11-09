from db import db

class EvaluacionIntegralCriterio(db.Model):
    __tablename__ = 'evaluacion_integral_criterios'
    id_criterio = db.Column(db.Integer, primary_key=True)
    id_apartado = db.Column(db.Integer, db.ForeignKey('evaluacion_integral_apartados.id_apartado'), nullable=False)
    id_grado = db.Column(db.Integer, db.ForeignKey('grados.id_grado'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    orden = db.Column(db.Integer, default=0)
    resultados = db.relationship('EvaluacionIntegralResultado', backref='criterio', cascade='all, delete-orphan')
