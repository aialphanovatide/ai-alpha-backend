import jwt
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from services.email.email import EmailService
from decorators.token_required import token_required
from config import Admin, Session, Role, AdminRole, Token
from flask import Blueprint, current_app, request, jsonify

dashboard_access_bp = Blueprint('dashboard_access_bp', __name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        "role": string (optional, default: "admin")
    }

    Returns:
    - 201: Admin registered successfully
    - 400: Invalid role or missing required field
    - 409: Email or username already exists
    - 500: Database error or unexpected error
    """
    data = request.json
    response = {"message": None, "error": None, "admin_id": None, "token": None}
    
    try:
        # Validate role
        role_name = data.get('role', 'admin').lower()
        if role_name not in ['superadmin', 'admin']:
            return jsonify({"error": "Invalid role"}), 400

        with Session() as session:
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
            role = session.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                session.add(role)
                session.flush()
            
            admin_role = AdminRole(admin_id=new_admin.admin_id, role_id=role.id)
            session.add(admin_role)

            # Generate token
            token = jwt.encode(
                {'admin_id': new_admin.admin_id},
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            session.commit()
        
        # Send welcome email
        email_service = EmailService()
        email_service.send_registration_confirmation(new_admin.email, new_admin.username)
        
        response["message"] = "Admin registered successfully and welcome email sent"
        response["admin_id"] = new_admin.admin_id
        response["token"] = token
        return jsonify(response), 201

    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400

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
        - 500: Database error or unexpected error
    """
    data = request.json
    session = Session()
    response = {"message": None, "error": None, "admin_id": None, "token": None}
    status_code = 500  # Default to server error

    try:
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
    """
    Delete an admin.
    
    Args:
        admin_id (int): The ID of the admin to delete
    
    Returns:
        JSON response with status code:
        - 200: Admin deleted successfully
        - 404: Admin not found
        - 500: Database error or unexpected error
    """
    response = {"message": None, "error": None}
    status_code = 500  # Default to server error
    with Session as session:
        try:
            admin = session.query(Admin).get(admin_id)
            if admin:
                session.query(AdminRole).filter_by(admin_id=admin_id).delete()
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
        finally:
            session.close()

        return jsonify(response), status_code


@dashboard_access_bp.route('/admin/request-password-reset', methods=['POST'])
def request_password_reset():
    """
    Request a password reset for an admin user.

    This endpoint generates a password reset token and sends it to the admin's email.

    Request JSON:
    {
        "email": string
    }

    Returns:
    - 200: Password reset email sent
    - 400: Missing required field
    - 404: Admin not found
    - 500: Database error or unexpected error
    """
    data = request.json
    
    try:
        with Session() as session:
            admin = session.query(Admin).filter_by(email=data['email']).first()
            if not admin:
                return jsonify({"error": "Admin not found"}), 404

            reset_token = jwt.encode(
                {'admin_id': admin.admin_id},
                current_app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            admin.reset_token = reset_token
            admin.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
            session.commit()

        email_service = EmailService()
        email_service.send_password_reset(admin.email, reset_token)

        return jsonify({"message": "Password reset email sent"}), 200

    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@dashboard_access_bp.route('/admin/reset-password', methods=['POST'])
def reset_password():
    """
    Reset an admin user's password.

    This endpoint resets the password for an admin user using a valid reset token.

    Request JSON:
    {
        "reset_token": string,
        "new_password": string
    }

    Returns:
    - 200: Password reset successful
    - 400: Invalid or expired reset token, or missing required field
    - 500: Database error or unexpected error
    """
    data = request.json
    
    try:
        reset_token = data['reset_token']
        new_password = data['new_password']

        try:
            payload = jwt.decode(reset_token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            admin_id = payload['admin_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Reset token has expired"}), 400
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid reset token"}), 400

        with Session() as session:
            admin = session.query(Admin).get(admin_id)
            if not admin or admin.reset_token != reset_token:
                return jsonify({"error": "Invalid reset token"}), 400

            admin.password = new_password
            admin.reset_token = None
            admin.reset_token_expires_at = None
            session.commit()

        return jsonify({"message": "Password reset successful"}), 200

    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500