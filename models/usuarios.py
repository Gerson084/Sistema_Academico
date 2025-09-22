from db import db


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    identificador = db.Column(db.String(100))  
    password = db.Column(db.String(100))
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(15))
    rol = db.Column(db.String(20))  
    activo = db.Column(db.Boolean)
    fecha_creacion = db.Column(db.DateTime)
    ultimo_acceso = db.Column(db.DateTime)

    def __init__(self, usuario, identificador, password, nombres, apellidos, email, telefono, rol, activo, fecha_creacion, ultimo_acceso):
        self.usuario = usuario
        self.identificador = identificador
        self.password = password
        self.nombres = nombres
        self.apellidos = apellidos
        self.email = email
        self.telefono = telefono
        self.rol = rol
        self.activo = activo
        self.fecha_creacion = fecha_creacion
        self.ultimo_acceso = ultimo_acceso