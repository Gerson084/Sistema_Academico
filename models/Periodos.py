from db import db

class Periodo(db.Model):
    __tablename__ = 'periodos'

    id_periodo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_ano_lectivo = db.Column(db.Integer, db.ForeignKey('anos_lectivos.id_ano_lectivo'), nullable=False)
    numero_periodo = db.Column(db.Integer, nullable=False)
    nombre_periodo = db.Column(db.String(50), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, default=False)

    # Relación con Año Lectivo
    ano_lectivo = db.relationship("AnoLectivo", backref="periodos")

    def __repr__(self):
        return f'<Periodo {self.nombre_periodo} - Año {self.ano_lectivo.ano if self.ano_lectivo else "N/A"}>'
    
    def to_dict(self):
        """Convertir el modelo a diccionario para JSON"""
        return {
            'id_periodo': self.id_periodo,
            'id_ano_lectivo': self.id_ano_lectivo,
            'numero_periodo': self.numero_periodo,
            'nombre_periodo': self.nombre_periodo,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'activo': self.activo
        }
    
    @staticmethod
    def crear_periodo(id_ano_lectivo, numero_periodo, nombre_periodo, fecha_inicio, fecha_fin, activo=False):
        """Método estático para crear un nuevo período"""
        nuevo_periodo = Periodo(
            id_ano_lectivo=id_ano_lectivo,
            numero_periodo=numero_periodo,
            nombre_periodo=nombre_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=activo
        )
        db.session.add(nuevo_periodo)
        db.session.commit()
        return nuevo_periodo
    
    def actualizar(self, **kwargs):
        """Actualizar datos del período"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
    
    def activar(self):
        """Activar período"""
        self.activo = True
        db.session.commit()
    
    def desactivar(self):
        """Desactivar período"""
        self.activo = False
        db.session.commit()