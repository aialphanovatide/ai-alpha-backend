import jwt
from functools import wraps
from config import Session, Token, Admin
from flask import request, jsonify

def token_logout(f):
    """
    Decorator to log out an admin by invalidating their Bearer token.

    This decorator checks for the presence of a Bearer token in the 
    Authorization header of the request. If the token is valid, it 
    invalidates the token and allows the request to proceed by calling 
    the original function. If the token is missing, invalid, or expired, 
    it returns a 401 Unauthorized response.

    Args:
        f (function): The original function to be decorated.

    Returns:
        function: The decorated function that checks for a valid 
        Bearer token and invalidates it before executing the original function.

    Raises:
        Unauthorized: Returns a JSON response with an error message 
        and a 401 status code if the token is missing, invalid, or 
        expired.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        bearer_token = request.headers.get('Authorization')
        if not bearer_token:
            return jsonify({"error": "Authorization header is missing"}), 401
        
        parts = bearer_token.split()
        if parts[0].lower() != 'bearer':
            return jsonify({"error": "Authorization header must start with Bearer"}), 401
        
        if len(parts) == 1:
            return jsonify({"error": "Token not found"}), 401
        
        if len(parts) > 2:
            return jsonify({"error": "Authorization header must be Bearer token"}), 401
        
        token = parts[1]
        
        try:
            with Session() as session:
                # Check if the token exists
                token_data = session.query(Token).filter_by(token=token).first()
                if not token_data:
                    return jsonify({"error": "Invalid token"}), 401
                
                # Invalidate the token
                session.delete(token_data)
                session.commit()
                
                # Call the original function and return its response
                return f(*args, **kwargs)  # This will call the logout_admin function
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
    return decorated


def token_required(f):
    """
    Decorator to verify the Bearer token in the Authorization header.

    This decorator checks for the presence of a Bearer token in the 
    Authorization header of the request. If the token is valid, it 
    allows the request to proceed by calling the original function. 
    If the token is missing, invalid, or expired, it returns a 401 
    Unauthorized response.

    Args:
        f (function): The original function to be decorated.

    Returns:
        function: The decorated function that checks for a valid 
        Bearer token before executing the original function.

    Raises:
        Unauthorized: Returns a JSON response with an error message 
        and a 401 status code if the token is missing, invalid, or 
        expired.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        bearer_token = request.headers.get('Authorization')
        if not bearer_token:
            return jsonify({"error": "Authorization header is missing"}), 401
        
        parts = bearer_token.split()
        if parts[0].lower() != 'bearer':
            return jsonify({"error": "Authorization header must start with Bearer"}), 401
        
        if len(parts) == 1:
            return jsonify({"error": "Token not found"}), 401
        
        if len(parts) > 2:
            return jsonify({"error": "Authorization header must be Bearer token"}), 401
        
        token = parts[1]
        
        # Verify the token using the Admin model
        admin = Admin.verify_token(token)
        if not admin:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Attach the admin to the request context if needed.
        request.admin = admin
        
        return f(*args, **kwargs)  # Call the original function
    return decorated