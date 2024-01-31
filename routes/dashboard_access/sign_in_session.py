from config import Admin
from flask import jsonify, session as flask_session
from flask import request
from config import Session as DBSession 
from flask import Blueprint

sign_in = Blueprint('signIn', __name__)

@sign_in.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')


        # Verifica las credenciales en la base de datos
        with DBSession() as db_session:
            try:
                user = db_session.query(Admin).filter_by(username=username).one()
                # Comparar contraseñas directamente
                if user.password == password:
                    # Autenticación exitosa, puedes devolver datos del usuario y otras cosas que puedas necesitar en el cliente
                    return jsonify({'success': True, 'user': {'admin_id': user.admin_id, 'username': user.username, 'email': user.mail}})
                else:
                    # Contraseña incorrecta
                    return jsonify({'success': False, 'message': 'Invalid password'})
            except:
                # Usuario no encontrado
                return jsonify({'success': False, 'message': 'Invalid username'})