from flask import Blueprint, render_template
from models.usuarios import Usuario


# Devuelve un enrutador
#user es el nombre del blueprint
users = Blueprint('user', __name__, template_folder="templates")

@users.route("/user_index")
def user_index():
    user_list = Usuario.query.all()
    return render_template("usuarios/user_index.html")