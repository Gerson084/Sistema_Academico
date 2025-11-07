from db import db

class Inasistencia(db.Model):
    __tablename__ = 'inasistencias'

    id_inasistencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id_estudiante', ondelete='CASCADE'), nullable=False)
    id_ano_lectivo = db.Column(db.Integer, db.ForeignKey('anos_lectivos.id_ano_lectivo', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    razon = db.Column(db.Text)
    justificada = db.Column(db.Boolean, nullable=False, default=False)
    fecha_registro = db.Column(db.TIMESTAMP, nullable=True)

    def __repr__(self):
        return f"<Inasistencia {self.id_inasistencia} - Estudiante {self.id_estudiante} - Fecha {self.fecha}>"
