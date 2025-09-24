from db import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    identificador = db.Column(db.String(100))
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(15))
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id_rol'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)

    def set_password(self, password):
        """Guardar contraseña encriptada"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Validar contraseña"""
        return check_password_hash(self.password, password)

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