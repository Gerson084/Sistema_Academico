from db import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class Calificacion(db.Model):
    __tablename__ = 'calificaciones'
    
    # Definir la llave única compuesta para prevenir duplicados
    __table_args__ = (
        UniqueConstraint('id_estudiante', 'id_asignacion', 'id_periodo', 'id_tipo_evaluacion', 
                        name='uk_calificacion_unica'),
    )

    id_calificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id_estudiante'), nullable=False)
    id_asignacion = db.Column(db.Integer, db.ForeignKey('materia_seccion.id_asignacion'), nullable=False)
    id_periodo = db.Column(db.Integer, db.ForeignKey('periodos.id_periodo'), nullable=False)
    id_tipo_evaluacion = db.Column(db.Integer, db.ForeignKey('tipos_evaluacion.id_tipo_evaluacion'), nullable=False)
    nota = db.Column(db.Numeric(4, 2), nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    # Relación con estudiante (permite acceder a calificacion.estudiante)
    estudiante = db.relationship('Estudiante', backref='calificaciones', lazy=True)
    # Relación con periodo (permite acceder a calificacion.periodo)
    periodo = db.relationship('Periodo', backref='calificaciones', lazy=True)
