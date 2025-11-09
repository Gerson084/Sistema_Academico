from db import db
from sqlalchemy import Enum

class EvaluacionIntegralResultado(db.Model):
    __tablename__ = 'evaluacion_integral_resultados'
    id_resultado = db.Column(db.Integer, primary_key=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id_estudiante'), nullable=False)
    id_criterio = db.Column(db.Integer, db.ForeignKey('evaluacion_integral_criterios.id_criterio'), nullable=False)
    id_periodo = db.Column(db.Integer, db.ForeignKey('periodos.id_periodo'), nullable=False)
    valoracion = db.Column(Enum('PA','PM','PB','NE', name='valoracion_enum'), nullable=False)
    id_maestro = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    fecha_registro = db.Column(db.DateTime, server_default=db.func.current_timestamp())
