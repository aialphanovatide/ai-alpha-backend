from flask import jsonify, request
from config import Admin, session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

from flask import Blueprint

sign_in = Blueprint('signIn', __name__)

@sign_in.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':

        try:
            data = request.json
            identifier = data.get('username')
            password = data.get('password')
        
            try:
                # Check if the identifier is an email
                user = session.query(Admin).filter_by(mail=identifier).one()
            except NoResultFound:
                try:
                    # If not found, check if the identifier is a username
                    user = session.query(Admin).filter_by(username=identifier).one()
                except NoResultFound:
                    # If neither email nor username is found, return an error
                    return jsonify({'success': False, 'message': 'Invalid email or username'}), 401

            # If user is found, compare the password
            if user.password == password:
                return jsonify({'success': True, 'user': {'admin_id': user.admin_id, 'username': user.username, 'email': user.mail}}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid password'}), 401
        
        except SQLAlchemyError as exc:
             session.rollback()
             return jsonify({'success': False, 'message': f'Database error: {str(exc)}'}), 500
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'message': f'{str(e)}'}), 500
