import secrets
import string
from sqlalchemy import exc
from sqlalchemy.orm import joinedload
from flask import jsonify, request, Blueprint
from config import PurchasedPlan, Session, User
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from routes.user.custom_classes import UserRegistrationSchema, UserEditSchema

user_bp = Blueprint('user', __name__)

def generate_unique_short_token(length=7, max_attempts=100):
    characters = string.ascii_letters + string.digits
    
    with Session() as session:
        for _ in range(max_attempts):
            token = ''.join(secrets.choice(characters) for _ in range(length))
            if not session.query(User).filter_by(auth_token=token).first():
                return token
    
    raise ValueError(f"Unable to generate a unique token after {max_attempts} attempts")


@user_bp.route('/user', methods=['POST'])
def set_new_user():
    """
    Register a new user in the system.

    This endpoint handles the registration process for a new user by processing
    the provided JSON data. It validates the input, generates a unique authentication token,
    and stores the user information in the database.

    Request JSON:
        - full_name (str): The full name of the user.
        - nickname (str): The nickname or username of the user.
        - email (str): The email address of the user.
        - email_verified (bool, optional): Whether the email has been verified. Defaults to False.
        - picture (str, optional): URL to the user's profile picture.
        - auth0id (str, optional): The Auth0 ID of the user.
        - provider (str, optional): The authentication provider used.
        - birth_date (str, optional): The birth date of the user.

    Returns:
        Response: JSON response with the following structure:
            - success (bool): Indicates if the operation was successful.
            - message (str): A descriptive message about the result of the operation.
            - user (dict): The complete newly created user object, if successful.

    Status Codes:
        - 201: User successfully created.
        - 400: Invalid or missing data in the request.
        - 409: User with this email or nickname already exists.
        - 500: Internal server error or database error.
    """
    response = {'success': False, 'message': None}
    schema = UserRegistrationSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        response['message'] = err.messages
        return jsonify(response), 400

    with Session() as session:
        try:
            token = generate_unique_short_token()
            new_user = User(auth_token=token, **data)
            session.add(new_user)
            session.commit()

            response = {
                'success': True,
                'message': 'User created successfully',
                'user': new_user.as_dict()
            }
            return jsonify(response), 201

        except IntegrityError as e:
            session.rollback()
            response['message'] = 'User with this email or nickname already exists'
            return jsonify(response), 409

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'An error occurred while creating the user: {str(e)}'
            return jsonify(response), 500

        except Exception as e:
            session.rollback()
            response['message'] = f'An unexpected error occurred: {str(e)}'
            return jsonify(response), 500
    
    
@user_bp.route('/user/<int:user_id>', methods=['PUT'])
def edit_user_data(user_id):
    """
    Edit user data identified by user ID.

    Args:
        user_id (int): ID of the user to edit.

    Request Body:
        JSON object with the following optional fields:
        - full_name (str): New full name for the user.
        - nickname (str): New nickname for the user.
        - birth_date (str): New birth date for the user.

    Returns:
        JSON: Updated user data and operation status.

    Response Codes:
        200: User data updated successfully.
        400: Invalid data provided for update.
        404: User not found.
        409: Conflict (e.g., nickname already taken).
        500: Internal server error.
    """
    schema = UserEditSchema()
    response = {'success': False, 'message': None, 'data': None}

    with Session() as session:
        try:
            data = schema.load(request.json)
          
            if not data:
                response['message'] = 'No valid data provided for update'
                return jsonify(response), 400

            user = session.query(User).filter_by(user_id=user_id).first()
           
            if not user:
                response['message'] = 'User not found'
                return jsonify(response), 404

            for key, value in data.items():
                setattr(user, key, value)

            session.commit()

            response['success'] = True
            response['message'] = 'User data updated successfully'
            response['data'] = user.as_dict()
            return jsonify(response), 200

        except ValidationError as err:
            response['message'] = err.messages
            return jsonify(response), 400

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error occurred. Possible duplicate nickname: {str(e)}'
            return jsonify(response), 409

        except Exception as e:
            session.rollback()
            response['message'] = f'An unexpected error occurred: {str(e)}'
            return jsonify(response), 500
    

@user_bp.route('/users', methods=['GET'])
def get_all_users_with_plans():
    """
    Retrieve all users with their purchased plans, with optional pagination.

    Query Parameters:
        page (int): Page number (optional)
        limit (int): Number of items per page (optional, max: 100)

    Returns:
        JSON: List of users with their plans, pagination info (if applicable), and operation status.

    Response Codes:
        200: Successful operation, returns list of users with plans.
        400: Invalid pagination parameters.
        500: Internal server error.
    """
    response = {'success': False, 'data': None, 'message': None, 'pagination': None}

    # Parse pagination parameters
    page = request.args.get('page', type=int)
    limit = request.args.get('limit', type=int)

    with Session() as session:
        try:
            # Base query
            query = session.query(User).options(joinedload(User.purchased_plans)).order_by(User.user_id)

            # Apply pagination if both page and limit are provided
            if page is not None and limit is not None:
                if page < 1 or limit < 1:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid pagination parameters'
                    }), 400

                limit = min(limit, 100)  # Cap at 100 items per page
                total_users = query.count()
                users = query.offset((page - 1) * limit).limit(limit).all()

                # Prepare pagination info
                total_pages = (total_users + limit - 1) // limit
                pagination = {
                    'page': page,
                    'limit': limit,
                    'total_items': total_users,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
                response['pagination'] = pagination
            else:
                # If no pagination parameters, return all users
                users = query.all()

            # Prepare result data
            result = [
                {
                    **user.as_dict(),
                    'purchased_plans': [plan.as_dict() for plan in user.purchased_plans]
                }
                for user in users
            ]

            response['success'] = True
            response['data'] = result
            response['message'] = f"{len(result)} users retrieved successfully"

            return jsonify(response), 200

        except SQLAlchemyError as e:
            session.rollback()
            return jsonify({
                'success': False,
                'message': 'An error occurred while retrieving user data'
            }), 500

        except Exception as e:
            session.rollback()
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred'
            }), 500


@user_bp.route('/user', methods=['GET'])
def get_user_with_plans():
    """
    Retrieve a specific user with their purchased plans.

    Query Parameters:
        user_id (int): ID of the user to retrieve.
        email (str): Email address of the user to retrieve.
        nickname (str): Nickname of the user to retrieve.
        auth0id (str): Auth0 ID of the user to retrieve.

    Returns:
        JSON: User data with plans and operation status.

    Response Codes:
        200: Successful operation, returns user data with plans.
        400: User identifier not provided or invalid.
        404: User not found.
        500: Internal server error.
    """
    response = {'success': False, 'data': None, 'message': None}

    with Session() as session:
        try:
            # Extract user identifier
            user_id = request.args.get('user_id')
            email = request.args.get('email')
            nickname = request.args.get('nickname')
            auth0id = request.args.get('auth0id')

            if not any([user_id, email, nickname, auth0id]):
                response['message'] = 'Valid user identifier not provided'
                return jsonify(response), 400

            # Prepare query with eager loading of purchased plans
            query = session.query(User).options(joinedload(User.purchased_plans))

            # Apply filter based on provided identifier
            if user_id:
                user = query.filter(User.user_id == int(user_id)).first()
            elif email:
                user = query.filter(User.email == email).first()
            elif nickname:
                user = query.filter(User.nickname == nickname).first()
            elif auth0id:
                user = query.filter(User.auth0id == auth0id).first()
            else:
                user = None

            if not user:
                response['message'] = 'User not found'
                return jsonify(response), 404

            # Prepare user data including purchased plans
            user_data = user.as_dict()
            user_data['purchased_plans'] = [plan.as_dict() for plan in user.purchased_plans]

            response['success'] = True
            response['data'] = user_data
            response['message'] = 'User retrieved successfully'
            return jsonify(response), 200
        
        except IntegrityError as e:
            session.rollback()
            response['message'] = f'Integrity error: {str(e)}'
            return jsonify(response), 500

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500

        except Exception as e:
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500


@user_bp.route('/package', methods=['POST'])
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
    with Session() as session:
        try:
            data = request.json
            
            # Validar que los campos obligatorios estén presentes
            required_fields = ['reference_name', 'price', 'auth0id', 'is_subscribed']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                response['message'] = f'Missing required fields: {", ".join(missing_fields)}'
                return jsonify(response), 400
            
            # Buscar el usuario por auth0id para obtener el user_id
            user = session.query(User).filter_by(auth0id=data['auth0id']).first()
            if not user:
                response['message'] = f"User not found for the provided Auth0 ID: {data['auth0id']}"
                return jsonify(response), 404
            
            new_plan = PurchasedPlan(
                reference_name=data.get('reference_name'),
                price=data.get('price'),
                is_subscribed=data.get('is_subscribed'),
                user_id=user.user_id
            )

            session.add(new_plan)
            session.commit()
            
            response['success'] = True
            response['message'] = 'Package saved successfully'
            return jsonify(response), 200
        
        except IntegrityError as e:
            session.rollback()
            response['message'] = f'Integrity error: {str(e)}'
            return jsonify(response), 500
                    
        except exc.SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
        
        except Exception as e:
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500
    

@user_bp.route('/package', methods=['PUT'])
def unsubscribe_package():
    """
    Unsubscribe a user from a purchased plan by setting is_subscribed to False.
    The record is kept for analysis purposes.
    
    Args:
        auth0id (str): Auth0 ID of the user.
        reference_name (str): Reference name of the purchased plan.

    Response:
        200: User unsubscribed from package successfully.
        400: Missing required fields (auth0id, reference_name) or already unsubscribed.
        404: Package not found or user not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    with Session() as session:
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['auth0id', 'reference_name']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                response['message'] = f'Missing required fields: {", ".join(missing_fields)}'
                return jsonify(response), 400
            
            # Find the user by auth0id
            user = session.query(User).filter_by(auth0id=data['auth0id']).first()
            if not user:
                response['message'] = f"User not found for the provided Auth0 ID: {data['auth0id']}"
                return jsonify(response), 404
            
            # Find the plan by reference_name and user_id
            plan = session.query(PurchasedPlan).filter_by(
                user_id=user.user_id, 
                reference_name=data['reference_name']
            ).first()
            if not plan:
                response['message'] = ' '
                return jsonify(response), 404
            
            # Check if the plan is already unsubscribed
            if not plan.is_subscribed:
                response['message'] = 'User is already unsubscribed from this package'
                return jsonify(response), 400
            
            # Update the subscription status
            plan.is_subscribed = False
            session.commit()
            
            response['success'] = True
            response['message'] = 'User unsubscribed from package successfully'
            return jsonify(response), 200
        
        except IntegrityError as e:
            session.rollback()
            response['message'] = f'Integrity error: {str(e)}'
            return jsonify(response), 500
                    
        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
        
        except Exception as e:
            session.rollback()
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500
    

@user_bp.route('/user', methods=['DELETE'])
def delete_user_account():
    """
    Delete a user account identified by auth0id or email.

    Request JSON:
        auth0id (str, optional): Full or partial auth0id of the user to delete.
        email (str, optional): Email of the user to delete.
        
    Note: At least one of auth0id or email must be provided.

    Response:
        200: User account deleted successfully.
        400: Neither auth0id nor email provided.
        404: User not found.
        500: Internal server error.
    """
    response = {'success': False, 'message': None}
    with Session() as session:
        try:
            data = request.get_json()
            auth0id = data.get('auth0id')
            email = data.get('email')

            if not auth0id and not email:
                response['message'] = 'Either auth0id or email must be provided'
                return jsonify(response), 400
            
            # Search for the user using auth0id (exact match) or email (exact match)
            query = session.query(User)
            if auth0id:
                query = query.filter(User.auth0id == auth0id)
            if email:
                query = query.filter(User.email == email)
            
            user = query.first()
            
            if not user:
                response['message'] = 'User not found'
                return jsonify(response), 404

            # Handle purchased plans
            purchased_plans = session.query(PurchasedPlan).filter(PurchasedPlan.user_id == user.user_id).all()
            for plan in purchased_plans:
                session.delete(plan)

            session.delete(user)
            session.commit()
            
            response['success'] = True
            response['message'] = 'User account and associated data deleted successfully'
            return jsonify(response), 200

        except SQLAlchemyError as e:
            session.rollback()
            response['message'] = f'Database error: {str(e)}'
            return jsonify(response), 500
        
        except Exception as e:
            session.rollback()
            response['message'] = f'Unexpected error: {str(e)}'
            return jsonify(response), 500
