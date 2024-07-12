from sqlalchemy import exc
from config import PurchasedPlan, session, User
from flask import jsonify, request, Blueprint
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def set_new_user():
    """
    Create a new user with provided data.

    Args:
        nickname (str): User's nickname.
        email (str): User's email.
        email_verified (bool): Whether the user's email is verified.
        picture (str): URL of the user's profile picture.
        auth0id (str): Auth0 ID of the user.
        provider (str): Authentication provider of the user.

    Response:
        200: User created successfully.
        400: Missing required fields (nickname, email).
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    try:
        data = request.json
        
        # Validar que los campos obligatorios estén presentes
        required_fields = ['nickname', 'email']
        for field in required_fields:
            if field not in data:
                response['message'] = f'Missing required field: {field}'
                return jsonify(response), 400
        
        new_user = User(
            nickname=data.get('nickname'),
            email=data.get('email'),
            email_verified=data.get('email_verified', True),
            picture=data.get('picture'),
            auth0id=data.get('auth0id'),
            provider=data.get('provider'),
            created_at=datetime.now()
        )

        session.add(new_user)
        session.commit()
        
        response['success'] = True
        response['message'] = 'User created successfully'
        return jsonify(response), 200
                
    except exc.SQLAlchemyError as e:
        session.rollback()
        response['message'] = f'Database error: {str(e)}'
        return jsonify(response), 500
    
    except Exception as e:
        response['message'] = str(e)
        return jsonify(response), 500


@user_bp.route('/edit_user/<int:user_id>', methods=['PUT'])
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
        
        user = session.query(User).filter_by(user_id=user_id).first()
        
        if not user:
            response['message'] = 'User not found'
            return jsonify(response), 404
        
        # Actualizar los campos si están presentes en los datos recibidos
        if 'nickname' in data:
            user.nickname = data['nickname']
        if 'email' in data:
            user.email = data['email']
        if 'email_verified' in data:
            user.email_verified = data['email_verified']
        if 'picture' in data:
            user.picture = data['picture']
        if 'auth0id' in data:
            user.auth0id = data['auth0id']
        if 'provider' in data:
            user.provider = data['provider']
        if 'created_at' in data:
            user.created_at = data['created_at']

        session.commit()
        
        response['success'] = True
        response['message'] = 'User data updated successfully'
        return jsonify(response), 200
                
    except exc.SQLAlchemyError as e:
        session.rollback()
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
        users_with_plans = session.query(User).join(PurchasedPlan).distinct(User.user_id).all()
        
        result = []
        for user in users_with_plans:
            user_data = {
                'user_id': user.user_id,
                'nickname': user.nickname,
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

    Response:
        200: Successful operation, returns user data with plans.
        400: User identifier not provided.
        404: User not found or user has no active plans.
        500: Internal server error.
    """
    response = {'success': False, 'data': None, 'message': None}
    try:
        user_id = request.args.get('user_id')
        email = request.args.get('email')
        nickname = request.args.get('nickname')
        
        query = session.query(User).outerjoin(PurchasedPlan)
        
        if not any([user_id, email, nickname]):
            response['message'] = 'User identifier not provided'
            return jsonify(response), 400
        
        if user_id:
            user = query.filter(User.user_id == user_id).first()
        elif email:
            user = query.filter(User.email == email).first()
        elif nickname:
            user = query.filter(User.nickname == nickname).first()
        
        if not user:
            response['message'] = 'User not found'
            return jsonify(response), 404
        
        user_data = {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'email': user.email,
            'email_verified': user.email_verified,
            'picture': user.picture,
            'auth0id': user.auth0id,
            'provider': user.provider,
            'created_at': user.created_at,
            'purchased_plans': []
        }
        
        has_active_plans = False
        for plan in user.purchased_plans:
            if plan.is_subscribed:
                has_active_plans = True
                plan_data = {
                    'product_id': plan.product_id,
                    'reference_name': plan.reference_name,
                    'price': plan.price,
                    'is_subscribed': plan.is_subscribed,
                    'created_at': plan.created_at
                }
                user_data['purchased_plans'].append(plan_data)
        
        if not has_active_plans:
            response['message'] = 'User does not have active plans'
            return jsonify(response), 404
        
        response['success'] = True
        response['data'] = user_data
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


@user_bp.route('/unsubscribe_package/<int:product_id>', methods=['PUT'])
def unsubscribe_package(product_id):
    """
    Unsubscribe a user from a purchased plan identified by product ID.
    Args:
        product_id (int): ID of the purchased plan to unsubscribe from.
    Response:
        200: User unsubscribed from package successfully.
        404: Package not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    try:
        # Buscar el plan por ID
        plan = session.query(PurchasedPlan).filter_by(product_id=product_id).first()
        
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
