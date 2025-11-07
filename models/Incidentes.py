from db import db
from datetime import datetime
from sqlalchemy import Enum


class Incidente(db.Model):
    __tablename__ = 'incidentes_disciplinarios'

    id_incidente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id_estudiante', ondelete='RESTRICT'), nullable=False)
    id_reportado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='RESTRICT'), nullable=False)
    id_periodo = db.Column(db.Integer, db.ForeignKey('periodos.id_periodo', ondelete='RESTRICT'), nullable=False)
    fecha_incidente = db.Column(db.DateTime, nullable=False)
    lugar = db.Column(db.String(100))
    tipo_incidente = db.Column(db.Enum('Agresión Física','Agresión Verbal','Bullying','Vandalismo','Indisciplina','Otro', name='tipo_incidente_enum'), nullable=False)
    descripcion = db.Column(db.Text)
    medidas_tomadas = db.Column(db.Text)
    testigos = db.Column(db.String(255))
    fecha_registro = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<Incidente {self.id_incidente} - Estudiante {self.id_estudiante} - Tipo {self.tipo_incidente}>"
