from flask import Blueprint, render_template, request,redirect, url_for, jsonify
from models.roles import Rol
from db import db



rol = Blueprint('rol', __name__, template_folder="templates")

rol.route('/rol_index')
def home():
    list_rol = Rol.query.all()
    return render_template("usuarios/user_index.html", list_rol = list_rol)


@rol.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        nombre_rol = request.form['nombre']
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        nuevo_rol = Rol(
            nombre_rol=nombre_rol, 
            descripcion=descripcion)
        db.session.add(nuevo_rol)
        db.session.commit()
        return redirect(url_for('user.user_index'))
    
    return render_template("usuarios/user_index.html")

@rol.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    rol = Rol.query.get_or_404(id)
    if request.method == 'POST':
        rol.nombre_rol = request.form['nombre']
        rol.descripcion = request.form['descripcion']
        rol.estado = request.form['estado']

    
        rol.id_rol = id
        rol.nombre_rol = request.form.get['nombre']
        rol.descripcion = request.form.get['descripcion']
        rol.estado = request.form.get['estado']

        db.session.commit()

        return jsonify({
            "success": True,
            "mensaje": "Usuario actualizado correctamente.",
            "redirect": url_for('user.user_index')
        })
    
        

    return redirect(url_for('user.user_index'))