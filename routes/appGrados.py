from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.Grados import Grado
from models.Secciones import Seccion
from db import db
from sqlalchemy import text

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
    
    try:
        # Verificar si el grado tiene secciones asociadas
        secciones_count = Seccion.query.filter_by(id_grado=id).count()
        
        if secciones_count > 0:
            return jsonify({
                "success": False,
                "icon": "warning",
                "title": "No se puede eliminar",
                "mensaje": f"No se puede eliminar este grado porque tiene {secciones_count} sección(es) asociada(s). Elimina las secciones primero."
            })
        
        # Si no tiene secciones, eliminar
        grado = Grado.query.get_or_404(id)
        db.session.delete(grado)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "icon": "success",
            "mensaje": "Grado eliminado correctamente",
            "redirect": url_for('grados.lista_grados')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "icon": "error",
            "mensaje": f"Error al eliminar el grado: {str(e)}"
        })


# Activar / desactivar grado
@grados_bp.route('/toggle/<int:id>', methods=['POST'])
def toggle_grado(id):
    r = solo_admin()
    if r: return r
    
    try:
        grado = Grado.query.get_or_404(id)
        
        # Si se está intentando desactivar, verificar si tiene secciones activas
        if grado.activo:
            # Verificar si tiene secciones
            query = text("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN al.activo = 1 THEN 1 ELSE 0 END) as activas
                FROM secciones s
                JOIN anos_lectivos al ON s.id_ano_lectivo = al.id_ano_lectivo
                WHERE s.id_grado = :id_grado
            """)
            
            result = db.session.execute(query, {'id_grado': id}).first()
            
            if result.total > 0:
                if result.activas > 0:
                    mensaje = f"No se puede desactivar este grado porque tiene {result.activas} sección(es) en año(s) lectivo(s) activo(s). Desactiva o elimina las secciones primero."
                else:
                    mensaje = f"No se puede desactivar este grado porque tiene {result.total} sección(es) asociada(s) en años anteriores. Considera eliminar las secciones si ya no son necesarias."
                
                return jsonify({
                    "success": False,
                    "icon": "warning",
                    "title": "No se puede desactivar",
                    "mensaje": mensaje
                })
        
        # Cambiar el estado
        grado.activo = not grado.activo
        db.session.commit()
        
        estado = "activado" if grado.activo else "desactivado"
        
        return jsonify({
            "success": True,
            "icon": "success",
            "mensaje": f"Grado {estado} correctamente",
            "redirect": url_for('grados.lista_grados')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "icon": "error",
            "mensaje": f"Error al cambiar el estado del grado: {str(e)}"
        })
