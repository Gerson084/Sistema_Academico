from flask import Blueprint, render_template, request, jsonify, url_for
from models.usuarios import Usuario
from models.roles import Rol  # Importa el modelo de roles
from db import db
from datetime import datetime
from werkzeug.security import generate_password_hash

# Blueprint para usuarios
users = Blueprint('user', __name__, template_folder="templates")

# LISTAR
@users.route("/user_index")
def user_index():
    #Una lista de todos los usuarios
    user_list = Usuario.query.all()
    list_rol = Rol.query.all()  # Obtiene los roles 
    print(list_rol)
    return render_template("usuarios/user_index.html", user_list=user_list, list_rol=list_rol)

# CREAR
@users.route("/user/create", methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        identificador = request.form.get('identificador')
        usuario_val = request.form.get('usuario')
        email_val = request.form.get('email')
        password_raw = request.form.get('password')
        telefono_val = request.form.get('telefono')

        # Validaciones únicas
        if Usuario.query.filter_by(usuario=usuario_val).first():
            return jsonify({"success": False, "mensaje": "El usuario ya existe."})
        if Usuario.query.filter_by(email=email_val).first():
            return jsonify({"success": False, "mensaje": "El correo electrónico ya está registrado."})
        if Usuario.query.filter_by(identificador=identificador).first():
            return jsonify({"success": False, "mensaje": "El DUI ya está registrado."})
        if Usuario.query.filter_by(telefono=telefono_val).first():
            return jsonify({"success": False, "mensaje": "El teléfono ya está registrado."})
        if not usuario_val:
            return jsonify({"success": False, "mensaje": "El nombre de usuario es obligatorio."})
        if not email_val:
            return jsonify({"success": False, "mensaje": "El correo electrónico es obligatorio."})
        if not telefono_val:
            return jsonify({"success": False, "mensaje": "El teléfono es obligatorio."})
        if not identificador:
            return jsonify({"success": False, "mensaje": "El DUI es obligatorio."})
        if not password_raw:
            return jsonify({"success": False, "mensaje": "La contraseña es obligatoria."})

        nuevo = Usuario(
            usuario=usuario_val,
            password=generate_password_hash(password_raw),
            identificador=identificador,
            nombres=request.form.get('nombres'),
            apellidos=request.form.get('apellidos'),
            email=email_val,
            telefono=request.form.get('telefono'),
            id_rol=int(request.form.get('id_rol')),
            activo=request.form.get('activo') == '1',
            fecha_creacion=datetime.utcnow(),
            ultimo_acceso=None
        )
        db.session.add(nuevo)
        db.session.commit()

        return jsonify({
            "success": True,
            "mensaje": "Usuario creado correctamente.",
            "redirect": url_for('user.user_index')
        })

    return render_template("usuarios/user_form.html", user=None)

# EDITAR
@users.route("/user/edit/<int:id>", methods=['GET', 'POST'])
def edit_user(id):
    user = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        identificador = request.form.get('identificador')
        usuario_val = request.form.get('usuario')
        email_val = request.form.get('email')
        password_raw = request.form.get('password')



        # Validaciones únicas
        if Usuario.query.filter(Usuario.usuario==usuario_val, Usuario.id_usuario!=id).first():
            return jsonify({"success": False, "mensaje": "El usuario ya existe."})
        if Usuario.query.filter(Usuario.email==email_val, Usuario.id_usuario!=id).first():
            return jsonify({"success": False, "mensaje": "El correo electrónico ya está registrado."})
        if Usuario.query.filter(Usuario.identificador==identificador, Usuario.id_usuario!=id).first():
            return jsonify({"success": False, "mensaje": "El DUI ya está registrado."})
        if not usuario_val:
            return jsonify({"success": False, "mensaje": "El nombre de usuario es obligatorio."})
        if not identificador:
            return jsonify({"success": False, "mensaje": "El DUI es obligatorio."})

        user.usuario = usuario_val
        if password_raw:
            user.password = generate_password_hash(password_raw)
        user.identificador = identificador
        user.nombres = request.form.get('nombres')
        user.apellidos = request.form.get('apellidos')
        user.email = email_val
        user.telefono = request.form.get('telefono')
        user.id_rol = int(request.form.get('id_rol'))
        user.activo = request.form.get('activo') == '1'
        user.ultimo_acceso = datetime.utcnow()

        db.session.commit()

        return jsonify({
            "success": True,
            "mensaje": "Usuario actualizado correctamente.",
            "redirect": url_for('user.user_index')
        })

    return render_template("usuarios/user_form.html", user=user)

# DESACTIVAR (en vez de eliminar)
@users.route("/user/deactivate/<int:id>", methods=['POST'])
def deactivate_user(id):
    user = Usuario.query.get_or_404(id)
    
    # Verificar si el usuario ya está inactivo
    if not user.activo:
        return jsonify({
            "success": False,
            "mensaje": "El usuario ya está inactivo."
        })
    
    # Desactivar el usuario en lugar de eliminarlo
    user.activo = False
    user.ultimo_acceso = datetime.utcnow()
    
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Usuario desactivado correctamente.",
        "redirect": url_for('user.user_index')
    })
# ACTIVAR (nuevo método para reactivar)
@users.route("/user/activate/<int:id>", methods=['POST'])
def activate_user(id):
    user = Usuario.query.get_or_404(id)
    
    # Verificar si el usuario ya está activo
    if user.activo:
        return jsonify({
            "success": False,
            "mensaje": "El usuario ya está activo."
        })
    
    # Activar el usuario
    user.activo = True
    user.ultimo_acceso = datetime.utcnow()
    
    db.session.commit()

    return jsonify({
        "success": True,
        "mensaje": "Usuario activado correctamente.",
        "redirect": url_for('user.user_index')
    })
