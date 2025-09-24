from db import db

class Rol(db.Model):
    __tablename__ = 'roles'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='activo')

    def __repr__(self):
        return f"<Rol {self.nombre_rol}>"
