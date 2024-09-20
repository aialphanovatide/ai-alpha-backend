import jwt
from config import Admin
from config import Session
from functools import wraps
from flask import request, jsonify
from sqlalchemy.orm import joinedload

def require_superadmin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization token is missing"}), 401
        
        parts = auth_header.split()
        if parts[0].lower() != 'bearer':
            return jsonify({"error": "Authorization header must start with Bearer"}), 401
        
        if len(parts) == 1:
            return jsonify({"error": "Token not found"}), 401
        
        if len(parts) > 2:
            return jsonify({"error": "Authorization header must be Bearer token"}), 401
        
        token = parts[1]
        
        try:
            admin = Admin.verify_token(token)  # Verify the token
            if not admin:
                return jsonify({"error": "Invalid token"}), 401
            
            # Use a new session to access roles
            with Session() as session:
                # Eager load roles
                admin = session.query(Admin).options(joinedload(Admin.roles)).get(admin.admin_id)
                if not admin or 'superadmin' not in [role.name for role in admin.roles]:
                    return jsonify({"error": "Superadmin privileges required"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated