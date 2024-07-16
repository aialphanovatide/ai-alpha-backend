from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from config import db
from functools import wraps


def create_response(success=False, data=None, error=None, **kwargs):
    response = {
        'success': success,
        'data': data,
        'error': error,
        **kwargs
    }
    return response



def handle_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            db.session.commit()
            return response
        except SQLAlchemyError as e:
            db.session.rollback()
            response = create_response(error=f"Database error: {str(e)}")
            return jsonify(response), 500
        except Exception as e:
            db.session.rollback()
            response = create_response(error=f"Internal server error: {str(e)}")
            return jsonify(response), 500
        finally:
            db.session.close()
    return wrapper

