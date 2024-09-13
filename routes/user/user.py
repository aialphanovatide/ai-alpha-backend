import secrets
import string
from sqlalchemy import exc
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, request, Blueprint
from config import PurchasedPlan, session, User

user_bp = Blueprint('user', __name__)

def generate_unique_short_token(length=7, max_attempts=100):
    characters = string.ascii_letters + string.digits
    
    for _ in range(max_attempts):
        token = ''.join(secrets.choice(characters) for _ in range(length))
        if not session.query(User).filter_by(auth_token=token).first():
            return token
    
    raise ValueError(f"Unable to generate a unique token after {max_attempts} attempts")

@user_bp.route('/register', methods=['POST'])
def set_new_user():
    response = {'success': False, 'message': None}
    try:
        data = request.json
        
        required_fields = ['full_name', 'nickname', 'email']
        for field in required_fields:
            if field not in data:
                response['message'] = f'Missing required field: {field}'
                return jsonify(response), 400
        
        new_user = User(
            full_name=data.get('full_name'),
            nickname=data.get('nickname'),
            email=data.get('email'),
            email_verified=data.get('email_verified', False),
            picture=data.get('picture'),
            auth0id=data.get('auth0id'),
            provider=data.get('provider')
        )

        session.add(new_user)
        session.commit()

        try:
            token = generate_unique_short_token()
        except ValueError as e:
            response['message'] = str(e)
            return jsonify(response), 500

        new_user.auth_token = token
        session.commit()
        
        response['success'] = True
        response['message'] = 'User created successfully'
        response['auth_token'] = token
        return jsonify(response), 200
                
    except SQLAlchemyError as e:
        session.rollback()
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500
    
  
@user_bp.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user_data(user_id):
    """
    Edit user data identified by user ID.

    Args:
        user_id (int): ID of the user to edit.

    Response:
        200: User data updated successfully.
        400: Missing user ID or no data provided to update.
        404: User not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    try:
        data = request.json
        
        # Allow for editing full_name and nickname
        if not any(key in data for key in ['full_name', 'nickname']):
            response['message'] = 'No valid fields provided for update'
            return jsonify(response), 400
        
        user = session.query(User).filter(User.auth0id.like(f'%{user_id}%')).first()
        
        if not user:
            response['message'] = 'User not found'
            return jsonify(response), 404
        
        # Update only allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'nickname' in data:
            user.nickname = data['nickname']

        session.commit()
        
        response['success'] = True
        response['message'] = 'User data updated successfully'
        return jsonify(response), 200
                
    except exc.SQLAlchemyError as e:
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500
    

@user_bp.route('/users', methods=['GET'])
def get_all_users_with_plans():
    """
    Retrieve all users with their purchased plans.

    Response:
        200: Successful operation, returns list of users with plans.
        500: Internal server error.
    """
    response = {'success': False, 'data': None, 'message': None}
    try:
        # Realizar una consulta con un outer join para incluir todos los usuarios
        users_with_plans = session.query(User).outerjoin(PurchasedPlan).all()
        
        result = []
        for user in users_with_plans:
            # Preparar los datos del usuario
            user_data = {
                'user_id': user.user_id,
                'nickname': user.nickname,
                'full_name': user.full_name,
                'email': user.email,
                'email_verified': user.email_verified,
                'picture': user.picture,
                'auth0id': user.auth0id,
                'provider': user.provider,
                'created_at': user.created_at,
                'purchased_plans': []
            }
            
            # Agregar los planes del usuario si existen
            if user.purchased_plans:
                for plan in user.purchased_plans:
                    plan_data = {
                        'product_id': plan.product_id,
                        'reference_name': plan.reference_name,
                        'price': plan.price,
                        'is_subscribed': plan.is_subscribed,
                        'created_at': plan.created_at
                    }
                    user_data['purchased_plans'].append(plan_data)
            
            # Agregar la información del usuario a la lista de resultados
            result.append(user_data)
        
        response['success'] = True
        response['data'] = result
        return jsonify(response), 200

    except exc.SQLAlchemyError as e:
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500


@user_bp.route('/user', methods=['GET'])
def get_user_with_plans():
    """
    Retrieve a specific user with their purchased plans.

    Args (at least one required):
        user_id (int): ID of the user to retrieve.
        email (str): Email address of the user to retrieve.
        nickname (str): Nickname of the user to retrieve.
        auth0id (str): Auth0 ID of the user to retrieve.

    Response:
        200: Successful operation, returns user data with plans.
        400: User identifier not provided.
        404: User not found.
        500: Internal server error.
    """
    response = {'success': False, 'data': None, 'message': None}
    try:
        user_id = request.args.get('user_id')
        email = request.args.get('email')
        nickname = request.args.get('nickname')
        full_name = request.args.get('full_name')
        auth0id = request.args.get('auth0id')
        
        query = session.query(User).outerjoin(PurchasedPlan)
        
        if not any([user_id, email, nickname, auth0id]):
            response['message'] = 'User identifier not provided'
            return jsonify(response), 400
        
        if user_id:
            user = query.filter(User.user_id == user_id).first()
        elif email:
            user = query.filter(User.email == email).first()
        elif nickname:
            user = query.filter(User.nickname == nickname).first()
        elif auth0id:
            user = query.filter(User.auth0id == auth0id).first()
        elif full_name:
            user = query.filter(User.full_name == full_name).first()
        
        if not user:
            response['message'] = 'User not found'
            return jsonify(response), 404
        
        user_data = {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'full_name': user.full_name,
            'email': user.email,
            'email_verified': user.email_verified,
            'picture': user.picture,
            'auth0id': user.auth0id,
            'provider': user.provider,
            'created_at': user.created_at,
            'purchased_plans': []
        }
        
        for plan in user.purchased_plans:
            plan_data = {
                'product_id': plan.product_id,
                'reference_name': plan.reference_name,
                'price': plan.price,
                'is_subscribed': plan.is_subscribed,
                'created_at': plan.created_at
            }
            user_data['purchased_plans'].append(plan_data)
        
        response['success'] = True
        response['data'] = user_data
        
        # Check if user has no active plans
        if not user.purchased_plans:
            response['message'] = 'User does not have any purchased plans'
            return jsonify(response), 200
        
        return jsonify(response), 200

    except exc.SQLAlchemyError as e:
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500


@user_bp.route('/purchase_plan', methods=['POST'])
def save_package():
    """
    Save a new purchased plan for a user.

    Args:
        reference_name (str): Reference name of the purchased plan.
        price (float): Price of the plan.
        is_subscribed (bool, optional): Subscription status (default True).
        user_id (int): ID of the user purchasing the plan.
        auth0id (str): Auth0 ID of the user purchasing the plan.
        
    Response:
        200: Package saved successfully.
        400: Missing required fields (reference_name, price, user_id, auth0id).
        404: User not found for provided auth0id.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    try:
        data = request.json
        
        # Validar que los campos obligatorios estén presentes
        required_fields = ['reference_name', 'price', 'auth0id']
        for field in required_fields:
            if field not in data:
                response['message'] = f'Missing required field: {field}'
                return jsonify(response), 400
        
        # Buscar el usuario por auth0id para obtener el user_id
        user = session.query(User).filter_by(auth0id=data['auth0id']).first()
        if not user:
            response['message'] = 'User not found for provided auth0id'
            return jsonify(response), 404
        
        new_plan = PurchasedPlan(
            reference_name=data.get('reference_name'),
            price=data.get('price'),
            is_subscribed=data.get('is_subscribed', True),
            user_id=user.user_id,  # Usar el user_id encontrado
            created_at=datetime.now()
        )

        session.add(new_plan)
        session.commit()
        
        response['success'] = True
        response['message'] = 'Package saved successfully'
        return jsonify(response), 200
                
    except exc.SQLAlchemyError as e:
        session.rollback()
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500
    

@user_bp.route('/unsubscribe_package', methods=['PUT'])
def unsubscribe_package():
    """
    Unsubscribe a user from a purchased plan identified by reference name and user auth0id.
    
    Args:
        auth0id (str): Auth0 ID of the user.
        reference_name (str): Reference name of the purchased plan.

    Response:
        200: User unsubscribed from package successfully.
        400: Missing required fields (auth0id, reference_name).
        404: Package not found or user not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    try:
        data = request.json
        
        # Validar que los campos obligatorios estén presentes
        required_fields = ['auth0id', 'reference_name']
        for field in required_fields:
            if field not in data:
                response['message'] = f'Missing required field: {field}'
                return jsonify(response), 400
        
        # Buscar el usuario por auth0id para obtener el user_id
        user = session.query(User).filter_by(auth0id=data['auth0id']).first()
        if not user:
            response['message'] = 'User not found for provided auth0id'
            return jsonify(response), 404
        
        # Buscar el plan por reference_name y user_id
        plan = session.query(PurchasedPlan).filter_by(user_id=user.user_id, reference_name=data['reference_name']).first()
        if not plan:
            response['message'] = 'Package not found'
            return jsonify(response), 404
        
        # Actualizar el estado de suscripción
        plan.is_subscribed = False  

        session.commit()
        
        response['success'] = True
        response['message'] = 'User unsubscribed from package successfully'
        return jsonify(response), 200
                
    except exc.SQLAlchemyError as e:
        session.rollback()
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500


@user_bp.route('/delete_user', methods=['DELETE'])
def delete_user_account():
    """
    Delete a user account identified by user ID.

    Args:
        user_id (str): Partial or full auth0id of the user to delete.

    Response:
        200: User account deleted successfully.
        404: User not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID not provided'}), 400
        
        # Buscar el usuario por ID parcial o completo usando like
        user = session.query(User).filter(User.auth0id.like(f'%{user_id}%')).first()
        
        if not user:
            response['message'] = 'User not found'
            return jsonify(response), 404

        # Eliminar el usuario de la base de datos
        session.delete(user)
        session.commit()
        
        response['success'] = True
        response['message'] = 'User account deleted successfully'
        return jsonify(response), 200

    except exc.SQLAlchemyError as e:
        session.rollback()
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500
