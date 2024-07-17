from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from config import Session
from http import HTTPStatus
from functools import wraps


def create_response(success: bool= False, data=None, error: str= None, **kwargs):
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
        session = Session()
        try:
            # Call the function with its original arguments
            response = func(*args, **kwargs)
            session.commit()
            return response
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Database error: {str(e)}")
            response = create_response(success=False, error=f"Database error: {str(e)}")
            return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            session.rollback()
            print(f"Internal server error: {str(e)}")
            response = create_response(success=False, error=f"Internal server error: {str(e)}")
            return jsonify(response), HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            session.close()
    return wrapper

