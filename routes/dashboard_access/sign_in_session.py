import os
import bcrypt
from config import Admin
from flask_cors import CORS
from websocket.socket import socketio
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 
from flask import Blueprint


sign_in = Blueprint('signIn', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)

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