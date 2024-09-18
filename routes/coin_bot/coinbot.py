import os
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from config import Category, CoinBot, Session, session
from datetime import datetime
from routes.category.category import are_fundamentals_complete, has_support_resistance_lines
from services.aws.s3 import ImageProcessor
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.exceptions import BadRequest

coin_bp = Blueprint('coin_bp', __name__)

AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET_ICONS = os.getenv('S3_BUCKET')

# Initialize the ImageProcessor
image_processor = ImageProcessor(aws_access_key=AWS_ACCESS, aws_secret_key=AWS_SECRET_KEY)

@coin_bp.route('/coin', methods=['POST'])
def create_coin():
    """
    Create a new coin bot in the database.

    This endpoint creates a new coin bot entry with the provided details and
    saves it to the database. It also handles the upload of an SVG icon to AWS S3.

    Request Form Data:
        name (str): The name of the coin bot (required)
        alias (str): An alternative identifier for the coin bot (required)
        category_id (int): The ID of the associated category (required)
        background_color (str): HEX code string for visual representation (optional)
        icon (file): An SVG file to be used as the coin bot icon (optional)

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - coin (dict or None): The created coin bot data or None
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 201: Created successfully
            - 400: Bad request (missing required fields or invalid SVG)
            - 404: Category not found
            - 500: Internal server error
    """
    response = {
        "success": False,
        "coin": None,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            name = request.form.get('name')
            alias = request.form.get('alias')
            category_id = request.form.get('category_id')
            background_color = request.form.get('background_color')
            icon_file = request.files.get('icon')
            symbol = request.files.get('symbol')
            
            if not name or not alias or not category_id:
                response["error"] = 'Name, alias, and category ID are required'
                status_code = 400
                return jsonify(response), status_code

            # Check if the category exists
            category = session.query(Category).get(category_id)
            if not category:
                response["error"] = f'Category with ID {category_id} not found'
                status_code = 404
                return jsonify(response), status_code

            icon_url = None
            if icon_file:
            # Normalize the alias
                normalized_alias = alias.strip().lower().replace(" ", "")
                icon_filename = secure_filename(f"{normalized_alias}.svg")
                icon_url = image_processor.upload_svg_to_s3(icon_file, S3_BUCKET_ICONS, icon_filename)
                if not icon_url:
                    response["error"] = 'Failed to upload SVG file'
                    status_code = 400
                    return jsonify(response), status_code

            new_coin = CoinBot(
                name=name,
                alias=alias,
                category_id=category_id,
                background_color=background_color,
                icon=icon_url,
                is_active=False,
                symbol=symbol,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            session.add(new_coin)
            session.commit()

            response["success"] = True
            response["coin"] = new_coin.as_dict()
            status_code = 201  # Created

        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error occurred: {str(e)}"
            status_code = 500
        except Exception as e:
            response["error"] = f"An unexpected error occurred: {str(e)}"
            status_code = 500

    return jsonify(response), status_code



@coin_bp.route('/coin/<int:coin_id>', methods=['PUT'])
def update_coin(coin_id):
    """
    Update a coin's information in the database.

    This function handles PUT requests to update the details of a specific coin,
    identified by its coin_id. It can update various fields including name, alias,
    category, background color, and icon.

    Args:
        coin_id (int): The ID of the coin to be updated.

    Returns:
        tuple: A tuple containing:
            - A JSON response with the following structure:
                {
                    "success": bool,
                    "coin": dict or None,
                    "error": str or None
                }
            - An HTTP status code (int)

    Raises:
        BadRequest: If no update data is provided.
        ValueError: If the provided category_id is invalid or if there's an error processing the icon.
        IntegrityError: If there's a database integrity violation.
        SQLAlchemyError: If a database error occurs.
        Exception: For any other unexpected errors.

    Note:
        This function interacts with the database using SQLAlchemy sessions and
        handles file operations for icon updates using S3 bucket storage.
    """
    response = {
        "success": False,
        "coin": None,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            data = request.json
            if not data:
                raise BadRequest('No update data provided')

            coin = session.query(CoinBot).get(coin_id)
            if not coin:
                response["error"] = f'Coin with ID {coin_id} not found'
                return jsonify(response), 404

            # Update fields if provided
            for field in ['name', 'alias', 'category_id', 'background_color']:
                if field in data:
                    setattr(coin, field, data[field])

            # Handle category change
            if 'category_id' in data:
                category = session.query(Category).get(data['category_id'])
                if not category:
                    raise ValueError(f"Category with ID {data['category_id']} not found")
                coin.category = category

            # Handle icon update
            if 'icon' in data:
                icon_svg_string = data['icon']
                try:
                    if coin.icon:  # Delete old icon if exists
                        old_icon_filename = coin.icon.split('/')[-1]
                        image_processor.delete_from_s3(bucket=S3_BUCKET_ICONS, image_url=old_icon_filename)

                    alias = coin.alias
                    normalized_alias = alias.strip().lower().replace(" ", "")
                    new_icon_filename = secure_filename(f"{normalized_alias}.svg")
                    icon_url = image_processor.upload_svg_to_s3(icon_svg_string, S3_BUCKET_ICONS, new_icon_filename)

                    if not icon_url:
                        raise ValueError('Failed to upload new SVG icon')

                    coin.icon = icon_url
                except Exception as e:
                    raise ValueError(f"Error processing icon: {str(e)}")

            session.commit()
            response["success"] = True
            response["coin"] = coin.as_dict()
            status_code = 200

        except BadRequest as e:
            response["error"] = str(e)
            status_code = 400
        except ValueError as e:
            response["error"] = str(e)
            status_code = 400
        except IntegrityError as e:
            session.rollback()
            response["error"] = f"Database integrity error: {str(e)}"
            status_code = 400
        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error occurred: {str(e)}"
            status_code = 500
        except Exception as e:
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            status_code = 500

    return jsonify(response), status_code

@coin_bp.route('/coins', methods=['GET'])
def get_all_coins():
    """
    Retrieve all coins from the database.

    This endpoint fetches all coin bots from the database and returns them as a list.
    If no coins are found, it returns an empty list.

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - coins (list): A list of dictionaries, each representing a coin bot
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Successfully retrieved coins (even if the list is empty)
            - 500: Internal server error
    """
    response = {
        "success": False,
        "coins": [],
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            coins = session.query(CoinBot.name).order_by(CoinBot.name).all()
            response["coins"] = [coin[0] for coin in coins]
            response["success"] = True
            status_code = 200
        except SQLAlchemyError as e:
            response["error"] = f"Database error occurred: {str(e)}"
        except Exception as e:
            response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code


@coin_bp.route('/coin/<int:coin_id>', methods=['DELETE'])
def delete_coin(coin_id):
    response = {
        "success": False,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            coin = session.query(CoinBot).get(coin_id)
            if not coin:
                response["error"] = f"No coin found with ID: {coin_id}"
                status_code = 404
                return jsonify(response), status_code

            if coin.icon:
                icon_filename = coin.icon.split('/')[-1]
                try:
                    image_processor.delete_from_s3(bucket=S3_BUCKET_ICONS, image_url=icon_filename)
                except Exception as e:
                    return jsonify({"success": False, "error": f"Error deleting icon from S3: {str(e)}"}), 500

            session.delete(coin)
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



@coin_bp.route('/coin/<int:coin_id>/toggle-publication', methods=['POST'])
def toggle_coin_publication(coin_id):
    response = {
        "success": False,
        "message": "",
        "is_active": False,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            coin = session.query(CoinBot).get(coin_id)
            if not coin:
                response["error"] = f"No coin found with ID: {coin_id}"
                status_code = 404
                return jsonify(response), status_code

            # If the coin is currently active, deactivate it
            if coin.is_active:
                coin.is_active = False
                coin.updated_at = datetime.now()
                session.commit()
                response["success"] = True
                response["message"] = "Coin deactivated successfully"
                response["is_active"] = False
                status_code = 200
            else:
                # Perform validations
                fundamentals_complete = are_fundamentals_complete(coin)
                chart = coin.chart[0] if coin.chart else None
                chart_valid = chart and has_support_resistance_lines(chart)

                if fundamentals_complete and chart_valid:
                    coin.is_active = True
                    coin.updated_at = datetime.now()
                    session.commit()
                    response["success"] = True
                    response["message"] = "Coin activated successfully"
                    response["is_active"] = True
                    status_code = 200
                else:
                    error_messages = []
                    if not fundamentals_complete:
                        error_messages.append("Fundamentals are incomplete")
                    if not chart_valid:
                        error_messages.append("Chart is missing support or resistance lines")
                    
                    response["error"] = ". ".join(error_messages)
                    status_code = 400

        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error occurred: {str(e)}"
            status_code = 500
        except Exception as e:
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            status_code = 500

    return jsonify(response), status_code