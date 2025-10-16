from db import db
from models.Calificaciones import Calificacion

from datetime import datetime

class PromedioPeriodo(db.Model):
    __tablename__ = 'promedios_periodo'

    id_promedio_periodo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_calificacion = db.Column(db.Integer, db.ForeignKey('calificaciones.id_calificacion'), nullable=False)
    promedio_actividades = db.Column(db.Numeric(4, 2))
    nota_rc = db.Column(db.Numeric(4, 2))
    promedio_integradoras = db.Column(db.Numeric(4, 2))
    nota_prueba_objetiva = db.Column(db.Numeric(4, 2))
    nota_actitud = db.Column(db.String(50))
    asistencia = db.Column(db.Numeric(4, 2))
    nota_final_periodo = db.Column(db.Numeric(4, 2))
    fecha_calculo = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con la tabla calificaciones
    calificacion = db.relationship('Calificacion', backref='promedios_periodo', lazy=True)

    def __repr__(self):
        return f'<PromedioPeriodo {self.id_promedio_periodo} - Actitud: {self.nota_actitud}>'
