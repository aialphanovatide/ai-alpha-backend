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

coin_bot_bp = Blueprint('coin_bot_bp', __name__)

AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_BUCKET_ICONS = os.getenv('S3_BUCKET')

# Initialize the ImageProcessor
image_processor = ImageProcessor(aws_access_key=AWS_ACCESS, aws_secret_key=AWS_SECRET_KEY)

@coin_bot_bp.route('/coin_bots', methods=['POST'])
def create_coin_bot():
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
            - coin_bot (dict or None): The created coin bot data or None
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 201: Created successfully
            - 400: Bad request (missing required fields or invalid SVG)
            - 404: Category not found
            - 500: Internal server error
    """
    response = {
        "success": False,
        "coin_bot": None,
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
                icon_filename = secure_filename(f"{alias}_coin.svg")
                icon_url = image_processor.upload_svg_to_s3(icon_file, S3_BUCKET_ICONS, icon_filename)
                if not icon_url:
                    response["error"] = 'Failed to upload SVG file'
                    status_code = 400
                    return jsonify(response), status_code

            new_coin_bot = CoinBot(
                name=name,
                alias=alias,
                category_id=category_id,
                background_color=background_color,
                icon=icon_url,
                is_active=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            session.add(new_coin_bot)
            session.commit()

            response["success"] = True
            response["coin_bot"] = new_coin_bot.as_dict()
            status_code = 201  # Created

        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error occurred: {str(e)}"
            status_code = 500
        except Exception as e:
            response["error"] = f"An unexpected error occurred: {str(e)}"
            status_code = 500

    return jsonify(response), status_code




@coin_bot_bp.route('/coins/<int:coin_id>', methods=['PUT'])
def update_coin(coin_id):
    response = {
        "success": False,
        "coin_bot": None,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            data = request.json
            if not data:
                raise BadRequest('No update data provided')

            coin_bot = session.query(CoinBot).get(coin_id)
            if not coin_bot:
                response["error"] = f'Coin with ID {coin_id} not found'
                return jsonify(response), 404

            # Update fields if provided
            for field in ['name', 'alias', 'category_id', 'background_color', 'is_active']:
                if field in data:
                    setattr(coin_bot, field, data[field])

            # Handle category change
            if 'category_id' in data:
                category = session.query(Category).get(data['category_id'])
                if not category:
                    raise ValueError(f"Category with ID {data['category_id']} not found")
                coin_bot.category = category

            # Handle icon update
            if 'icon' in data:
                icon_svg_string = data['icon']
                try:
                    if coin_bot.icon:  # Delete old icon if exists
                        old_icon_filename = coin_bot.icon.split('/')[-1]
                        image_processor.delete_from_s3(S3_BUCKET_ICONS, old_icon_filename)
                    
                    new_icon_filename = secure_filename(f"{coin_bot.alias or coin_bot.name}_coin_icon.svg")
                    icon_url = image_processor.upload_svg_to_s3(icon_svg_string, S3_BUCKET_ICONS, new_icon_filename)
                    if not icon_url:
                        raise ValueError('Failed to upload new SVG icon')
                    coin_bot.icon = icon_url
                except Exception as e:
                    raise ValueError(f"Error processing icon: {str(e)}")

            session.commit()
            response["success"] = True
            response["coin_bot"] = coin_bot.as_dict()
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




@coin_bot_bp.route('/coins/<int:coin_id>', methods=['DELETE'])
def delete_coin(coin_id):
    response = {
        "success": False,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            coin_bot = session.query(CoinBot).get(coin_id)
            if not coin_bot:
                response["error"] = f"No coin found with ID: {coin_id}"
                status_code = 404
                return jsonify(response), status_code

            if coin_bot.icon:
                icon_filename = coin_bot.icon.split('/')[-1]
                try:
                    image_processor.delete_from_s3(S3_BUCKET_ICONS, icon_filename)
                except Exception as e:
                    # Log the error, but continue with deletion
                    print(f"Error deleting icon from S3: {str(e)}")

            session.delete(coin_bot)
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



@coin_bot_bp.route('/coins/<int:coin_id>/toggle-publication', methods=['POST'])
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
            coin_bot = session.query(CoinBot).get(coin_id)
            if not coin_bot:
                response["error"] = f"No coin found with ID: {coin_id}"
                status_code = 404
                return jsonify(response), status_code

            # If the coin is currently active, deactivate it
            if coin_bot.is_active:
                coin_bot.is_active = False
                coin_bot.updated_at = datetime.now()
                session.commit()
                response["success"] = True
                response["message"] = "Coin deactivated successfully"
                response["is_active"] = False
                status_code = 200
            else:
                # Perform validations
                fundamentals_complete = are_fundamentals_complete(coin_bot)
                chart = coin_bot.chart[0] if coin_bot.chart else None
                chart_valid = chart and has_support_resistance_lines(chart)

                if fundamentals_complete and chart_valid:
                    coin_bot.is_active = True
                    coin_bot.updated_at = datetime.now()
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