from db import db


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    password = db.Column(db.String(100))
    identificador = db.Column(db.String(100))  
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(15))
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo = db.Column(db.Boolean)
    fecha_creacion = db.Column(db.DateTime)
    ultimo_acceso = db.Column(db.DateTime)

    def __init__(self, usuario, password, identificador, nombres, apellidos, email, telefono, id_rol, activo, fecha_creacion, ultimo_acceso):
        self.usuario = usuario
        self.password = password
        self.identificador = identificador
        self.nombres = nombres
        self.apellidos = apellidos
        self.email = email
        self.telefono = telefono
        self.id_rol = id_rol
        self.activo = activo
        self.fecha_creacion = fecha_creacion
        self.ultimo_acceso = ultimo_acceso