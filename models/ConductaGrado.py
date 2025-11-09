from db.cn import db
from datetime import datetime

class ConductaGradoPeriodo(db.Model):
    __tablename__ = 'conducta_grado_periodo'
    
    id_conducta_grado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id_estudiante', ondelete='CASCADE'), nullable=False)
    id_seccion = db.Column(db.Integer, db.ForeignKey('secciones.id_seccion', ondelete='CASCADE'), nullable=False)
    id_ano_lectivo = db.Column(db.Integer, db.ForeignKey('anos_lectivos.id_ano_lectivo', ondelete='CASCADE'), nullable=False)
    nota_conducta_final = db.Column(db.Numeric(4, 2), nullable=True)
    conducta_literal = db.Column(db.String(2), nullable=True)
    observacion_general = db.Column(db.Text, nullable=True)
    fecha_ingreso = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraint único
    __table_args__ = (
        db.UniqueConstraint('id_estudiante', 'id_seccion', 'id_ano_lectivo', 
                          name='uk_conducta_grado_unica'),
        db.Index('idx_conducta_seccion_ano', 'id_seccion', 'id_ano_lectivo'),
        db.Index('idx_conducta_estudiante', 'id_estudiante'),
    )
    
    def __repr__(self):
        return f'<ConductaGrado {self.id_conducta_grado}>'
