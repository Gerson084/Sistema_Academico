from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuarios import Usuario
from models.roles import Rol
from db import db
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        user = Usuario.query.filter_by(usuario=usuario, activo=True).first()

        if user and user.check_password(password):
            session['user_id'] = user.id_usuario
            session['user_name'] = user.nombres
            session['user_role'] = user.id_rol

            user.ultimo_acceso = datetime.datetime.utcnow()
            db.session.commit()

            if user.id_rol == 1:  # administrador
                return redirect(url_for('auth.dashboard_admin'))
            elif user.id_rol == 2:  # docente (puede ser también coordinador)
                return redirect(url_for('coordinador.dashboard'))
        else:
            flash("❌ Usuario o contraseña incorrectos", "danger")
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard/admin')
def dashboard_admin():
    if session.get('user_role') != 1:
        return redirect(url_for('auth.login'))
    return render_template('dashboards/admin_dashboard.html')


@auth_bp.route('/dashboard/docente')
def dashboard_docente():
    """Redirige al dashboard unificado de coordinador/docente"""
    if session.get('user_role') != 2:
        return redirect(url_for('auth.login'))
    # Redirigir al dashboard unificado
    return redirect(url_for('coordinador.dashboard'))
