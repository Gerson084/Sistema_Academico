from flask import Blueprint, render_template, request,redirect, url_for, jsonify
from models.roles import Rol
from db import db



rol = Blueprint('rol', __name__)

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
    rol = Rol.query.get_or_404(request.form['id'])
    # Do NOT allow changing the role name from this endpoint. Ignore any submitted nombre_rol.
    descripcion = request.form.get('descripcion')
    estado = request.form.get('estado')

    # Basic validation
    if not descripcion or not estado:
        return jsonify({"success": False, "mensaje": "Descripción y estado son obligatorios."}), 400

    # Only update mutable fields
    rol.descripcion = descripcion
    rol.estado = estado

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Rol actualizado correctamente.",
        "redirect": url_for('user.user_index')
    })
             
            
                

   

    return redirect(url_for('user.user_index'))
