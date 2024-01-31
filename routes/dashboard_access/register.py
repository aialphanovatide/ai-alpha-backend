from config import Admin
from flask import Flask, jsonify, session as flask_session
from flask import request
from config import Session as DBSession 
from flask import Blueprint


sign_up = Blueprint('signUp', __name__)

@sign_up.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        # Obtener datos del formulario
        data = request.json  # Utiliza request.json para obtener datos JSON directamente
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        print('pass: ', password)
        print('user: ', username)
        print('email: ', email)

        # Verificar que la contraseña no sea None
        if password is None:
            return jsonify({'success': False, 'message': 'Invalid password'})

        # Crear un nuevo objeto Admin y guardar en la base de datos
        new_admin = Admin(username=username, mail=email, password=password)

        # Utiliza la sesión de SQLAlchemy que has definido en config.py
        with DBSession() as db_session:
            db_session.add(new_admin)
            db_session.commit()

        # Puedes devolver un JSON indicando el éxito del registro
        return jsonify({'success': True, 'message': 'Registration successful'})

    # Si la solicitud no es POST, devolver un mensaje de error
    return jsonify({'success': False, 'message': 'Invalid request'})