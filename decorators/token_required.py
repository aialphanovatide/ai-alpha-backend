import jwt
from functools import wraps
from config import Session, Admin
from flask import request, jsonify, current_app, g

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401
        
        parts = auth_header.split()
        if parts[0].lower() != 'bearer':
            return jsonify({"error": "Authorization header must start with Bearer"}), 401
        
        if len(parts) == 1:
            return jsonify({"error": "Token not found"}), 401
        
        if len(parts) > 2:
            return jsonify({"error": "Authorization header must be Bearer token"}), 401
        
        token = parts[1]
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            with Session() as session:
                admin = session.query(Admin).get(data['admin_id'])
                if not admin:
                    return jsonify({"error": "Invalid token"}), 401
                g.current_admin = admin
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated