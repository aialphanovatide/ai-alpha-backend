from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from config import db_url, session
from functools import wraps

def create_response(success=False, data=None, error=None, **kwargs):
    """
    Creates a standardized response for API responses.

    :param success: Indicates if the operation was successful.
    :param data: The data to be returned in the response.
    :param error: Error message, if any.
    :param kwargs: Other additional parameters.
    :return: Dictionary with the formatted response.
    """
    response = {
        'success': success,
        'data': data,
        'error': error,
        **kwargs
    }
    return response

def handle_db_session(func):
    """
    Decorator to handle the database session.

    Wraps the function to manage the database session, ensuring 
    commit on success and rollback on error.

    :param func: The function to decorate.
    :return: Decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Execute the decorated function
            response = func(*args, **kwargs)
            # Commit the session if there are no errors
            session.commit()
            return response
        except SQLAlchemyError as e:
            # Rollback the session in case of a database error
            session.rollback()
            response = create_response(error=f"Database error: {str(e)}")
            return jsonify(response), 500
        except Exception as e:
            # Rollback the session in case of any other error
            session.rollback()
            response = create_response(error=f"Internal server error: {str(e)}")
            return jsonify(response), 500
        finally:
            # Close the session in any case
            session.close()
    return wrapper
