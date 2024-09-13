from sqlalchemy.exc import SQLAlchemyError
from config import Session
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
    return (response) 

def handle_db_session(func):
    """
    Decorator to handle the database session for functions.
    Wraps the function to manage the database session.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = Session()
        try:
            # Add session to kwargs so the decorated function can use it
            kwargs['session'] = session
            # Execute the decorated function
            result = func(*args, **kwargs)
            # Commit the session if there are no errors
            session.commit()
            # Return the result of the function call, wrapped in create_response
            return create_response(success=True, data=result)
        except SQLAlchemyError as e:
            # Rollback the session in case of a database error
            session.rollback()
            print(f"Database error: {str(e)}")
            return create_response(success=False, error="Database error occurred.")
        except Exception as e:
            # Rollback the session in case of any other error
            session.rollback()
            print(f"Internal server error: {str(e)}")
            return create_response(success=False, error="Internal server error occurred.")
        finally:
            # Close the session in any case
            session.close()
    return wrapper
