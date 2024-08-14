from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from config import Category, session

category_bp = Blueprint('category_bp', __name__)

@category_bp.route('/create_category', methods=['POST'])
def create_category():
    """
    Create a new category in the database.

    This endpoint creates a new category entry with the provided details and
    saves it to the database. It returns the created category data if successful.

    Request JSON:
    {
        "category": str,         # The main identifier for the category (required)
        "category_name": str,    # A user-friendly name for the category (optional)
        "time_interval": int,    # The time interval associated with the category (optional)
        "is_active": bool,       # Indicates if the category is currently active (optional, default: true)
        "border_color": str,     # The color used for visual representation (optional, default: 'No Color')
        "icon": str              # The icon or image associated with the category (optional, default: 'No Image')
    }

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - category (dict or None): The created category data or None
            - error (str or None): Error message, if any
        HTTP Status Code

    Raises:
        400 Bad Request: If required fields are missing
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "success": False,
        "category": None,
        "error": None
    }
    status_code = 500  # Default to server error

    try:
        data = request.json

        # Extract data from JSON
        category = data.get('category')
        category_name = data.get('category_name')
        time_interval = data.get('time_interval')
        is_active = data.get('is_active', True)
        border_color = data.get('border_color', 'No Color')
        icon = data.get('icon', 'No Image')

        # Validate data
        if not category:
            response["error"] = 'Category is required'
            status_code = 400
            return jsonify(response), status_code

        # Create a new instance of Category
        new_category = Category(
            category=category,
            category_name=category_name,
            time_interval=time_interval,
            is_active=is_active,
            border_color=border_color,
            icon=icon
        )

        # Add the category to the database
        session.add(new_category)
        session.commit()

        response["success"] = True
        response["category"] = new_category.as_dict()
        status_code = 200  # Created

    except SQLAlchemyError as e:
        session.rollback()  # Rollback in case of database error
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code

@category_bp.route('/delete_category/<string:category_alias>', methods=['DELETE'])
def delete_category(category_alias):
    """
    Delete a category from the database by its alias.

    This endpoint deletes a category entry identified by the provided alias.
    It returns a success message if the deletion is successful.

    Args:
        category_alias (str): The alias of the category to be deleted

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - error (str or None): Error message, if any
        HTTP Status Code

    Raises:
        404 Not Found: If no category is found with the provided alias
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "success": False,
        "error": None
    }
    status_code = 500  # Default to server error

    try:
        # Find the category to delete
        category = session.query(Category).filter_by(category_name=category_alias).first()

        if not category:
            response["error"] = f"No category found with alias: {category_alias}"
            status_code = 404
            return jsonify(response), status_code

        # Delete the category
        session.delete(category)
        session.commit()

        response["success"] = True
        status_code = 200  # OK

    except SQLAlchemyError as e:
        session.rollback()  # Rollback in case of database error
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code
