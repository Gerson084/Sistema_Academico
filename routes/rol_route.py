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
        if Rol.query.filter_by(nombre_rol=nombre_rol).first():
            return jsonify({
                "success": False,
                "mensaje": "El nombre del rol ya existe. Por favor, elige otro nombre."
            }), 400
        descripcion = request.form['descripcion']
        estado = request.form['estado']
        nuevo_rol = Rol(
            nombre_rol=nombre_rol,
            descripcion=descripcion,
            estado=estado)
        db.session.add(nuevo_rol)
        db.session.commit()
        return jsonify({
            "success": True,
            "mensaje": "Rol creado correctamente.",
            "redirect": url_for('user.user_index')
        })

    return render_template("usuarios/user_index.html")

@rol.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    rol = Rol.query.get_or_404(id)
    nombre_rol = request.form['nombre_rol']
    descripcion = request.form['descripcion']
    estado = request.form['estado']

    if not nombre_rol or not descripcion or not estado:
        return jsonify({
            "success": False,
            "mensaje": "Todos los campos son obligatorios."
        }), 400

    if nombre_rol != rol.nombre_rol:
        existing_rol = Rol.query.filter_by(nombre_rol=nombre_rol).first()
        if existing_rol:
            return jsonify({
                "success": False,
                "mensaje": "El nombre del rol ya existe. Por favor, elige otro nombre."
            }), 400

    rol.nombre_rol = nombre_rol
    rol.descripcion = descripcion
    rol.estado = estado

    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Rol actualizado correctamente.",
        "redirect": url_for('user.user_index')
    })
