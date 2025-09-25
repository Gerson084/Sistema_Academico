from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuarios import Usuario
from db import db
from werkzeug.security import generate_password_hash

change_password_bp = Blueprint('change_password', __name__)

@change_password_bp.route('/cambiar_contrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para cambiar la contraseña.', 'warning')
        return redirect(url_for('auth.login'))

    user = Usuario.query.get(session['user_id'])
    if request.method == 'POST':
        actual = request.form.get('actual')
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')

        if not user.check_password(actual):
            flash('La contraseña actual es incorrecta.', 'danger')
        elif nueva != confirmar:
            flash('Las contraseñas nuevas no coinciden.', 'danger')
        elif len(nueva) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres.', 'warning')
        else:
            user.password = generate_password_hash(nueva)
            db.session.commit()
            flash('Contraseña actualizada correctamente.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/change_password.html')
