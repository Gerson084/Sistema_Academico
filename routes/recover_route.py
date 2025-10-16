from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuarios import Usuario
from db import db
import random, string, datetime
try:
    from flask_mail import Message
except Exception:
    # Si flask_mail no está disponible, definimos un stub para no romper la ejecución.
    class Message:
        def __init__(self, *args, **kwargs):
            self.recipients = kwargs.get('recipients', [])
            self.body = ''
        def __setattr__(self, name, value):
            object.__setattr__(self, name, value)
from flask import current_app

recover_bp = Blueprint('recover', __name__)

# Diccionario temporal para almacenar códigos de recuperación
recovery_codes = {}

@recover_bp.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(email=email).first()
        if user:
            code = ''.join(random.choices(string.digits, k=6))
            recovery_codes[email] = {'code': code, 'expires': datetime.datetime.utcnow() + datetime.timedelta(minutes=10)}
            msg = Message('Código de recuperación', recipients=[email])
            msg.body = f'Tu código de recuperación es: {code}'
            from app import mail
            mail.send(msg)
        flash('Correo enviado, si su correo se encuentra registrado se le enviará el código para proceder con la recuperación de la contraseña.', 'info')
        return redirect(url_for('recover.recuperar'))
    return render_template('auth/recover.html')

@recover_bp.route('/verificar', methods=['GET', 'POST'])
def verificar():
    email = request.args.get('email')
    if request.method == 'POST':
        code = request.form.get('code')
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')
        data = recovery_codes.get(email)
        if not data or datetime.datetime.utcnow() > data['expires']:
            flash('El código ha expirado. Solicita uno nuevo.', 'danger')
            return redirect(url_for('recover.recuperar'))
        if code != data['code']:
            flash('Código incorrecto.', 'danger')
        elif nueva != confirmar:
            flash('Las contraseñas no coinciden.', 'danger')
        elif len(nueva) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres.', 'warning')
        else:
            user = Usuario.query.filter_by(email=email).first()
            if user:
                user.set_password(nueva)
                db.session.commit()
                recovery_codes.pop(email, None)
                flash('Contraseña actualizada. Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('auth.login'))
    return render_template('auth/verify_code.html', email=email)
