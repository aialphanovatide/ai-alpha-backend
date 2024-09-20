import jwt
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from services.email.email_service import EmailService
from decorators.token_required import token_required
from config import Admin, Session, Role, AdminRole, Token
from flask import Blueprint, current_app, flash, redirect, render_template, request, jsonify, url_for


dashboard_access_bp = Blueprint('dashboard_access_bp', __name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

email_service = EmailService(current_app)

@dashboard_access_bp.route('/admin/register', methods=['POST'])
def register_admin():
    """
    Register a new admin user.
    This endpoint creates a new admin user with the provided details and assigns the specified role.
    Request JSON:
    {
        "email": string,
        "username": string,
        "password": string,
        "role_id": integer
    }
    Returns:
    - 201: Admin registered successfully
    - 400: Invalid role or missing required field
    - 409: Email or username already exists
    - 500: Database error or unexpected error
    """
    data = request.json
    response = {"message": None, "error": None, "admin_id": None, "auth_token": None}

    # Check for required fields
    required_fields = ['username', 'email', 'password', 'role_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        with Session() as session:
            # Validate role
            role_id = data['role_id']
            role = session.query(Role).filter_by(id=role_id).first()
            if not role:
                return jsonify({"error": "Invalid role_id"}), 400

            # Check for existing admin
            existing_admin = session.query(Admin).filter(
                (Admin.email == data['email']) | (Admin.username == data['username'])
            ).first()
            if existing_admin:
                return jsonify({"error": "Email or username already exists"}), 409

            # Create new admin
            new_admin = Admin(
                email=data['email'],
                username=data['username'],
                password=data['password']
            )
            session.add(new_admin)
            session.flush()

            # Assign role
            admin_role = AdminRole(admin_id=new_admin.admin_id, role_id=role.id)
            session.add(admin_role)
            session.commit()

            email_service.send_registration_confirmation(new_admin.email, new_admin.username)
            response["message"] = "Admin registered successfully and welcome email sent"
            response["admin_id"] = new_admin.admin_id
            response["auth_token"] = new_admin.auth_token
            return jsonify(response), 201

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@dashboard_access_bp.route('/admin/login', methods=['POST'])
def login_admin():
    """
    Authenticate an admin.
    Args:
    username (str): Admin's username
    password (str): Admin's password
    Returns:
    JSON response with status code:
    - 200: Login successful
    - 401: Invalid credentials
    - 400: Missing required field
    - 500: Database error or unexpected error
    """
    data = request.json
    session = Session()
    response = {"message": None, "error": None, "admin_id": None, "token": None, "token_expires_at": None}
    status_code = 500  # Default to server error

    try:
        # Check for required fields
        if 'username' not in data or 'password' not in data:
            raise KeyError('username' if 'username' not in data else 'password')

        # Authenticate admin
        admin = session.query(Admin).filter_by(username=data['username']).first()
        if admin and admin.verify_password(data['password']):
            # Generate token
            token = admin.generate_token()
            session.add(token)
            session.commit()
            
            response["message"] = "Login successful"
            response["admin_id"] = admin.admin_id
            response["token"] = token.token
            response["token_expires_at"] = token.expires_at.isoformat()
            status_code = 200
        else:
            response["error"] = "Invalid credentials"
            status_code = 401

    except KeyError as e:
        response["error"] = f"Missing required field: {str(e)}"
        status_code = 400
    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        status_code = 500
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code


@dashboard_access_bp.route('/admin/logout', methods=['POST'])
@token_required
def logout_admin():
    """
    Log out an admin by invalidating their current token.

    Required Header:
        Authorization: The current authentication token

    Returns:
        JSON response with status code:
        - 200: Logout successful
        - 400: Invalid token
        - 500: Database error or unexpected error
    """
    session = Session()
    response = {"message": None, "error": None}
    status_code = 500  # Default to server error
    
    try:
        # Get and invalidate token
        token = request.headers.get('Authorization')
        token_obj = session.query(Token).filter_by(token=token).first()
        if token_obj:
            session.delete(token_obj)
            session.commit()
            response["message"] = "Logged out successfully"
            status_code = 200
        else:
            response["error"] = "Invalid token"
            status_code = 400

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        status_code = 500

    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    finally:
        session.close()

    return jsonify(response), status_code


@dashboard_access_bp.route('/admin/<int:admin_id>', methods=['GET'])
def get_admin(admin_id):
    """
    Retrieve admin information.
    
    Args:
        admin_id (int): The ID of the admin to retrieve
    
    Returns:
        JSON response with status code:
        - 200: Admin information retrieved successfully
        - 404: Admin not found
        - 500: Database error or unexpected error
    """
    session = Session()
    response = {"data": None, "error": None}
    status_code = 500  # Default to server error
    
    try:
        admin = session.query(Admin).get(admin_id)
        if admin:
            response["data"] = admin.to_dict()
            status_code = 200
        else:
            response["error"] = "Admin not found"
            status_code = 404
    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code


@dashboard_access_bp.route('/admin/<int:admin_id>', methods=['PUT'])
def update_admin(admin_id):
    """
    Update admin information.
    
    Args:
        admin_id (int): The ID of the admin to update
        email (str, optional): New email address
        username (str, optional): New username
        password (str, optional): New password
        role (str, optional): New role ('superadmin' or 'admin')
    
    Returns:
        JSON response with status code:
        - 200: Admin updated successfully
        - 400: Bad request (invalid data)
        - 404: Admin not found
        - 500: Database error or unexpected error
    """
    data = request.json
    session = Session()
    response = {"message": None, "error": None}
    status_code = 500  # Default to server error
    
    try:
        admin = session.query(Admin).get(admin_id)
        if admin:
            if 'email' in data:
                admin.email = data['email']
            if 'username' in data:
                admin.username = data['username']
            if 'password' in data:
                admin.password = data['password']
            if 'role' in data:
                new_role_name = data['role'].lower()
                if new_role_name not in ['superadmin', 'admin']:
                    response["error"] = "Invalid role"
                    status_code = 400
                    return jsonify(response), status_code
                new_role = session.query(Role).filter_by(name=new_role_name).first()
                if not new_role:
                    new_role = Role(name=new_role_name)
                    session.add(new_role)
                admin_role = session.query(AdminRole).filter_by(admin_id=admin.admin_id).first()
                if admin_role:
                    admin_role.role_id = new_role.id
                else:
                    new_admin_role = AdminRole(admin_id=admin.admin_id, role_id=new_role.id)
                    session.add(new_admin_role)
            session.commit()
            response["message"] = "Admin updated successfully"
            status_code = 200
        else:
            response["error"] = "Admin not found"
            status_code = 404
    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        status_code = 500
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500
    finally:
        session.close()

    return jsonify(response), status_code

@dashboard_access_bp.route('/admin/<int:admin_id>', methods=['DELETE'])
def delete_admin(admin_id):
    response = {"message": None, "error": None}
    status_code = 500  # Default to server error
    
    with Session() as session:
        try:
            admin = session.query(Admin).get(admin_id)
            if admin:
                session.delete(admin)
                session.commit()
                response["message"] = "Admin deleted successfully"
                status_code = 200
            else:
                response["error"] = "Admin not found"
                status_code = 404
        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error: {str(e)}"
            status_code = 500
        except Exception as e:
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            status_code = 500

    return jsonify(response), status_code

@dashboard_access_bp.route('/admin/request-password-reset', methods=['POST'])
def request_password_reset():
    """
    Handle password reset request for admin users.

    This function processes a POST request to initiate a password reset.
    It generates a reset token, creates a reset link, and sends an email
    to the admin with instructions to reset their password.

    Returns:
        JSON response with a success message or error details.
    """
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    session = Session()
    try:
        admin = session.query(Admin).filter_by(email=email).first()
        if not admin:
            return jsonify({"error": "No account found with that email"}), 404
        
        new_token = admin.generate_token()
        
        session.add(new_token)
        session.commit()
        
        reset_link = url_for('dashboard_access_bp.reset_password', token=new_token.token, _external=True)
        email_service.send_password_reset_email(admin.email, admin.username, reset_link)
                
        return jsonify({"message": "Password reset email sent"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
        
        

@dashboard_access_bp.route('/admin/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Handle password reset process for admin users.

    This function processes both GET and POST requests:
    - GET: Renders the password reset form.
    - POST: Processes the submitted form to reset the password.

    Args:
        token (str): The password reset token.

    Returns:
        For GET: Rendered HTML template for password reset.
        For POST: Redirect to login page on success or error page on failure.
    """
    with Session() as session:
        try:
            admin = Admin.verify_reset_token(token)

            if not admin:
                flash('The password reset link is invalid or has expired.', 'error')
                return redirect(url_for('dashboard_access.login_admin'))

            if request.method == 'POST':
                new_password = request.form['new_password']
                confirm_password = request.form['confirm_password']

                if new_password != confirm_password:
                    flash('Passwords do not match.', 'error')
                else:
                    admin.password = new_password
                    session.commit()
                    return redirect('https://dashboard-alpha-ai.vercel.app/#/login')

            return render_template('reset_password.html')
        except Exception as e:
            session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('dashboard_access.login_admin'))
        
        
@dashboard_access_bp.route('/admin/roles', methods=['GET'])
def get_admin_roles():
    """
    Get all admin roles.
    Returns:
        JSON response with status code:
        - 200: List of admin roles retrieved successfully
        - 500: Database error or unexpected error
    """
    response = {"roles": [], "error": None}
    status_code = 500  # Default to server error

    with Session() as session:
        try:
            roles = session.query(Role).all()
            response["roles"] = [{"id": role.id, "name": role.name, "description": role.description} for role in roles]
            status_code = 200
        except SQLAlchemyError as e:
            response["error"] = f"Database error: {str(e)}"
        except Exception as e:
            response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code