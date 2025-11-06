from db import db
from datetime import datetime
from models.Calificaciones import Calificacion


class PromedioAnual(db.Model):
    __tablename__ = 'promedios_anuales'

    id_promedio_anual = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_promedio_periodo = db.Column(db.Integer, db.ForeignKey('promedios_periodo.id_promedio_periodo'), nullable=False)
    id_periodo = db.Column(db.Integer, db.ForeignKey('periodos.id_periodo'), nullable=False)
    promedio_final = db.Column(db.Numeric(4, 2))
    # conducta_final eliminado
    estado_final = db.Column(db.Enum('Aprobado', 'Reprobado', 'Pendiente'), default='Pendiente')
    fecha_calculo = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    promedio_periodo = db.relationship('PromedioPeriodo', backref='promedios_anuales', lazy=True)
    periodo = db.relationship('Periodo', backref='promedios_anuales', lazy=True)

    def __repr__(self):
        return f'<PromedioAnual {self.id_promedio_anual}>'
