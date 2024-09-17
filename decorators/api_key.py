from functools import wraps
from flask import request, jsonify
from config import APIKey
from config import Session
from sqlalchemy import func


# Decorator to require an API key for a route
def require_api_key(f):
    """
    Decorator to require a valid API key for a route.

    This decorator checks for the presence of a valid API key in the request headers.
    If a valid key is found, it updates the last_used timestamp and allows the request to proceed.
    If the key is missing or invalid, it returns an appropriate error response.

    Args:
        f (function): The route function to be decorated.

    Returns:
        function: The decorated function that includes API key validation.

    Raises:
        Exception: If there's an error during the database operation.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401

        session = Session()
        try:
            api_key_obj = session.query(APIKey).filter_by(key=api_key).first()
            if api_key_obj:
                # Update last_used timestamp
                api_key_obj.last_used = func.now()
                session.commit()
                return f(*args, **kwargs)
            else:
                return jsonify({"error": "Invalid API key"}), 401
        except Exception as e:
            session.rollback()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()

    return decorated_function


def check_api_key():
    """
    Check if the API key is valid and update the last_used timestamp.

    This function checks for the presence of a valid API key in the request headers.
    If a valid key is found, it updates the last_used timestamp and allows the request to proceed.
    If the key is missing or invalid, it returns an appropriate error response.

    Returns:
        None: If the API key is valid and the last_used timestamp is updated.
        JSON response: If the API key is missing or invalid.
        JSON response: If there's an error during the database operation.
    """
    whitelist = ['/admin', '/api/alert/tv', '/slack/events', '/api-keys/']
    # Skip API key check for certain routes if needed
    if any(request.path.startswith(route) for route in whitelist):
        return None

    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({"error": "API key is missing"}), 401

    session = Session()
    try:
        api_key_obj = session.query(APIKey).filter_by(key=api_key).first()
        if api_key_obj:
            # Update last_used timestamp
            api_key_obj.last_used = func.now()
            session.commit()
            return None
        else:
            return jsonify({"error": "Invalid API key"}), 401
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        session.close()