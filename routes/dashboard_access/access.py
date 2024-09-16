from functools import wraps
from config import Admin, Session, Role, AdminRole, Token
from flask import Blueprint, g, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

dashboard_access_bp = Blueprint('dashboard_access_bp', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        session = Session()
        try:
            admin = Admin.verify_token(token)
            if not admin:
                return jsonify({"error": "Invalid or expired token"}), 401
            g.current_admin = admin
            return f(*args, **kwargs)
        finally:
            session.close()
    return decorated

@dashboard_access_bp.route('/admin/register', methods=['POST'])
def register_admin():
    """
    Register a new admin with a specified role.
    
    Args:
        email (str): Admin's email address
        username (str): Admin's username
        password (str): Admin's password
        role (str): Role name ('superadmin' or 'admin')
    
    Returns:
        JSON response with status code:
        - 201: Admin registered successfully
        - 400: Bad request (missing data or invalid role)
        - 409: Conflict (email or username already exists)
        - 500: Database error or unexpected error
    """
    data = request.json
    session = Session()
    response = {"message": None, "error": None, "admin_id": None, "token": None}
    status_code = 500  # Default to server error

    try:
        # Validate role
        role_name = data.get('role', 'admin').lower()
        if role_name not in ['superadmin', 'admin']:
            response["error"] = "Invalid role"
            return jsonify(response), 400

        # Check for existing admin
        existing_admin = session.query(Admin).filter(
            (Admin.email == data['email']) | (Admin.username == data['username'])
        ).first()
        if existing_admin:
            response["error"] = "Email or username already exists"
            return jsonify(response), 409

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
        token = new_admin.generate_token()
        session.add(token)
        session.commit()
        
        response["message"] = "Admin registered successfully"
        response["admin_id"] = new_admin.admin_id
        response["token"] = token.token
        status_code = 201

    except KeyError as e:
        session.rollback()
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
    session = Session()
    response = {"message": None, "error": None}
    status_code = 500  # Default to server error
    
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