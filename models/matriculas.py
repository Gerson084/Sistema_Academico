from db import db
from datetime import datetime


class Matricula(db.Model):
    """Modelo para representar la matrícula de un estudiante en una sección"""
    
    __tablename__ = 'matriculas'
    
    # Campos de la tabla
    id_matricula = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiantes.id_estudiante'), nullable=False)
    id_seccion = db.Column(db.Integer, db.ForeignKey('secciones.id_seccion'), nullable=False)
    fecha_matricula = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    estudiante = db.relationship("Estudiante", backref="matriculas", lazy=True)
    seccion = db.relationship("Seccion", backref="matriculas", lazy=True)

    def __repr__(self):
        return f'<Matrícula {self.id_matricula}: Estudiante {self.id_estudiante} en Sección {self.id_seccion}>'
    
    def to_dict(self):
        """Convertir el modelo a diccionario para JSON"""
        return {
            'id_matricula': self.id_matricula,
            'id_estudiante': self.id_estudiante,
            'id_seccion': self.id_seccion,
            'fecha_matricula': self.fecha_matricula.isoformat() if self.fecha_matricula else None,
            'activa': self.activa
        }
    
    @staticmethod
    def crear_matricula(id_estudiante, id_seccion, fecha_matricula=None, **kwargs):
        """Método estático para crear una nueva matrícula"""
        nueva_matricula = Matricula(
            id_estudiante=id_estudiante,
            id_seccion=id_seccion,
            fecha_matricula=fecha_matricula or datetime.utcnow().date(),
            **kwargs
        )
        db.session.add(nueva_matricula)
        db.session.commit()
        return nueva_matricula
    
    def actualizar(self, **kwargs):
        """Actualizar datos de la matrícula"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
    
    def desactivar(self):
        """Desactivar matrícula (soft delete)"""
        self.activa = False
        db.session.commit()
    
    def reactivar(self):
        """Reactivar matrícula"""
        self.activa = True
        db.session.commit()