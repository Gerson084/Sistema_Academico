from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.Grados import Grado
from db import db

grados_bp = Blueprint('grados', __name__, template_folder="templates")



# Decorador para restringir acceso solo a admin
def solo_admin():
    if not session.get('user_id') or session.get('user_role') != 1:
        flash('Acceso restringido solo para administradores.', 'danger')
        return redirect(url_for('auth.login'))
    return None

# Listar grados
@grados_bp.route('/')
def lista_grados():
    r = solo_admin()
    if r: return r
    grados = Grado.query.all()
    return render_template("grados/listar.html", grados=grados)


# Nuevo grado
@grados_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_grado():
    r = solo_admin()
    if r: return r
    if request.method == 'POST':
        nuevo = Grado(
            nombre_grado=request.form.get('nombre_grado'),
            nivel=request.form.get('nivel'),
            activo=True
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('grados.lista_grados', success='true', action='created'))
    return render_template("grados/nuevo.html")


# Editar grado
@grados_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_grado(id):
    r = solo_admin()
    if r: return r
    grado = Grado.query.get_or_404(id)
    if request.method == 'POST':
        grado.nombre_grado = request.form.get('nombre_grado')
        grado.nivel = request.form.get('nivel')
        db.session.commit()
        return redirect(url_for('grados.lista_grados', success='true', action='updated'))
    return render_template("grados/editar.html", grado=grado)


# Eliminar grado
@grados_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_grado(id):
    r = solo_admin()
    if r: return r
    grado = Grado.query.get_or_404(id)
    db.session.delete(grado)
    db.session.commit()
    return redirect(url_for('grados.lista_grados'))


# Activar / desactivar grado
@grados_bp.route('/toggle/<int:id>')
def toggle_grado(id):
    r = solo_admin()
    if r: return r
    grado = Grado.query.get_or_404(id)
    grado.activo = not grado.activo
    db.session.commit()
    return redirect(url_for('grados.lista_grados'))
