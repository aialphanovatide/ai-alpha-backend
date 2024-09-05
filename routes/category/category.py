import os
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from config import Category, CoinBot, session
from services.aws.s3 import ImageProcessor
from werkzeug.utils import secure_filename

category_bp = Blueprint('category_bp', __name__)


AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET_ICONS = os.getenv('S3_BUCKET')

# Initialize the ImageProcessor
image_processor = ImageProcessor(aws_access_key=AWS_ACCESS, aws_secret_key=AWS_SECRET_KEY)

@category_bp.route('/categories', methods=['POST'])
def create_category():
    """
    Create a new category in the database.

    This endpoint creates a new category entry with the provided details and
    saves it to the database. It also handles the upload of an SVG icon to AWS S3.

    Request Form Data:
        name (str): The main identifier for the category (required, not null)
        alias (str): An alternative identifier for the category (required, not null)
        border_color (str): HEX code string for visual representation (optional)
        icon (file): An SVG file to be used as the category icon (optional)

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - category (dict or None): The created category data or None
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 201: Created successfully
            - 400: Bad request (missing required fields or invalid SVG)
            - 500: Internal server error
    """
    response = {
        "success": False,
        "category": None,
        "error": None
    }
    status_code = 500

    try:
        name = request.form.get('name')
        alias = request.form.get('alias')
        border_color = request.form.get('border_color')
        icon_file = request.files.get('icon')

        if not name or not alias:
            response["error"] = 'Name and Alias are required and cannot be null'
            status_code = 400
            return jsonify(response), status_code

        icon_url = None
        if icon_file:
            icon_filename = secure_filename(f"{alias}.svg")
            icon_url = image_processor.upload_svg_to_s3(icon_file, S3_BUCKET_ICONS, icon_filename)
            if not icon_url:
                response["error"] = 'Failed to upload SVG file'
                status_code = 400
                return jsonify(response), status_code

        new_category = Category(
            name=name,
            alias=alias,
            border_color=border_color,
            icon=icon_url
        )

        session.add(new_category)
        session.commit()

        response["success"] = True
        response["category"] = new_category.as_dict()
        status_code = 201  # Created

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code

@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """
    Delete a category from the AI Alpha server.

    This endpoint deletes a category entry identified by the provided ID,
    removes associated SVG icons from S3, and handles associated data.

    Args:
        category_id (int): The ID of the category to be deleted

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Deleted successfully
            - 404: Category not found
            - 500: Internal Server Error
    """
    response = {
        "success": False,
        "error": None
    }
    status_code = 500

    try:
        # Start transaction
        session.begin_nested()

        # Find the category to delete
        category = session.query(Category).get(category_id)

        if not category:
            response["error"] = f"No category found with ID: {category_id}"
            status_code = 404
            return jsonify(response), status_code

        # Delete associated icon from S3
        if category.icon:
            icon_filename = category.icon.split('/')[-1]
            image_processor.delete_from_s3(S3_BUCKET_ICONS, icon_filename)

        # Handle associated data (e.g., CoinBots)
        associated_bots = session.query(CoinBot).filter_by(category_id=category_id).all()
        for bot in associated_bots:
            # Here you might want to deactivate bots or handle them as per your business logic
            bot.category_id = None  # Or set to a default category

        # Delete the category
        session.delete(category)

        # Commit the transaction
        session.commit()

        response["success"] = True
        status_code = 200

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code



@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """
    Update an existing category in the database.

    This endpoint updates a category entry with the provided details and
    saves the changes to the database. It also handles the update of the SVG icon in AWS S3 if provided.

    Args:
        category_id (int): The ID of the category to be updated

    Request JSON:
        name (str, optional): The main identifier for the category
        alias (str, optional): An alternative identifier for the category
        border_color (str, optional): HEX code string for visual representation
        icon (str, optional): SVG file string to be used as the category icon

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - category (dict or None): The updated category data or None
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Updated successfully
            - 400: Bad request (invalid data)
            - 404: Category not found
            - 500: Internal server error
    """
    response = {
        "success": False,
        "category": None,
        "error": None
    }
    status_code = 500

    try:
        category = session.query(Category).get(category_id)
        if not category:
            response["error"] = f'Category with ID {category_id} not found'
            status_code = 404
            return jsonify(response), status_code

        data = request.json
        if not data:
            response["error"] = 'No update data provided'
            status_code = 400
            return jsonify(response), status_code

        # Update fields if provided
        if 'name' in data:
            category.name = data['name']
        if 'alias' in data:
            category.alias = data['alias']
        if 'border_color' in data:
            category.border_color = data['border_color']

        # Handle icon update
        if 'icon' in data:
            icon_svg_string = data['icon']
            if category.icon:  # Delete old icon if exists
                old_icon_filename = category.icon.split('/')[-1]
                image_processor.delete_from_s3(S3_BUCKET_ICONS, old_icon_filename)
            
            new_icon_filename = secure_filename(f"{category.alias or category.name}_icon.svg")
            icon_url = image_processor.upload_svg_string_to_s3(icon_svg_string, S3_BUCKET_ICONS, new_icon_filename)
            if not icon_url:
                response["error"] = 'Failed to upload new SVG icon'
                status_code = 400
                return jsonify(response), status_code
            category.icon = icon_url

        session.commit()

        response["success"] = True
        response["category"] = category.as_dict()
        status_code = 200  # Updated

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code