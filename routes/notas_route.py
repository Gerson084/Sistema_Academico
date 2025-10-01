from flask import Blueprint, render_template

notas_bp = Blueprint('notas', __name__, template_folder='templates')

@notas_bp.route('/notas/ingresar-ejemplo', methods=['GET'])
def ingresar_notas_ejemplo():
    return render_template('notas/formato_notas.html')
