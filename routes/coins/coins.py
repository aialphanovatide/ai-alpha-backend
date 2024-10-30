import os
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from config import Category, CoinBot, Session
from services.aws.s3 import ImageProcessor
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
from routes.category.category import validate_coin
from services.coingecko.coingecko import get_coin_data
from redis_client.redis_client import cache_with_redis, update_cache_with_redis
from sqlalchemy import func

coin_bp = Blueprint('coin_bp', __name__)

S3_BUCKET_ICONS = os.getenv('S3_BUCKET_ICONS')

# Initialize the ImageProcessor
image_processor = ImageProcessor()

@coin_bp.route('/coin', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_coins', 'get_all_categories'])
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
        symbol (str): The symbol of the coin (optional)

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - coin (dict or None): The created coin bot data or None
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 201: Created successfully
            - 400: Bad request (missing required fields, invalid SVG, or name/alias already exists)
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
            symbol = request.form.get('symbol')
            
            if not name or not alias or not category_id or not symbol:
                response["error"] = 'Name, alias, symbol and category are required'
                status_code = 400
                return jsonify(response), status_code
            
            # Check if name or alias already exist (case-insensitive)
            existing_coin = session.query(CoinBot).filter(
                func.lower(CoinBot.name) == func.lower(name)
            ).first()
            if existing_coin:
                response["error"] = f'A coin with the name "{name}" already exists'
                status_code = 400
                return jsonify(response), status_code

            existing_coin = session.query(CoinBot).filter(
                func.lower(CoinBot.alias) == func.lower(alias)
            ).first()
            if existing_coin:
                response["error"] = f'A coin with the alias "{alias}" already exists'
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

            try:
                coin_list_result = get_coin_data(name=name.casefold().strip(), symbol=symbol.casefold().strip())
                if coin_list_result['success'] and coin_list_result['coin']:
                    gecko_id = coin_list_result['coin']['id']
                else:
                    gecko_id = '' 
            except Exception as e:
                response["error"] = f"Error fetching gecko_id: {str(e)}"
                status_code = 500
                return jsonify(response), status_code

            new_coin = CoinBot(
                name=name,
                alias=alias,
                category_id=category_id,
                background_color=background_color,
                icon=icon_url,
                is_active=False,
                symbol=symbol, 
                gecko_id=gecko_id,
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

@coin_bp.route('/coin/<int:coin_id>', methods=['GET'])
@cache_with_redis(expiration=21600)
def get_single_coin(coin_id):
    """
    Retrieve a single coin from the database with its full details, keywords, and blacklist.

    This endpoint fetches a specific coin bot from the database and returns it
    with full details, including related keywords and blacklist entries.

    Args:
        coin_id (int): The ID of the coin to retrieve.

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - coin (dict or None): A dictionary representing the coin bot with full details,
                                   including keywords and blacklist, or None if not found
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Successfully retrieved the coin
            - 404: Coin not found
            - 500: Internal server error
    """
    response = {
        "success": False,
        "coin": None,
        "error": None
    }
    status_code = 500

    try:
        with Session() as session:
            coin = session.query(CoinBot).options(
                joinedload(CoinBot.keywords),
                joinedload(CoinBot.blacklist),
                joinedload(CoinBot.category)
            ).get(coin_id)

            if not coin:
                response["error"] = f"Coin with ID {coin_id} not found"
                status_code = 404
            else:
                coin_dict = coin.as_dict()
                coin_dict['whitelist'] = [keyword.as_dict() for keyword in coin.keywords]
                coin_dict['blacklist'] = [item.as_dict() for item in coin.blacklist]
                response["coin"] = coin_dict
                response["success"] = True
                status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code


@coin_bp.route('/coin/<int:coin_id>', methods=['PUT'])
@update_cache_with_redis(related_get_endpoints=['get_single_coin', 'get_all_coins'])
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
            data = request.form
            icon_file = request.files.get('icon')
            if not data:
                raise BadRequest('No update data provided')

            coin = session.query(CoinBot).get(coin_id)
            if not coin:
                response["error"] = f'Coin with ID {coin_id} not found'
                return jsonify(response), 404

            # Update fields if provided
            for field in ['name', 'alias', 'category_id', 'background_color', 'symbol', 'gecko_id']:
                if field in data:
                    setattr(coin, field, data[field])

            # Handle category change
            if 'category_id' in data:
                category = session.query(Category).get(data['category_id'])
                if not category:
                    raise ValueError(f"Category with ID {data['category_id']} not found")
                coin.category = category

            if icon_file:
                try:
                    if coin.icon:  # Delete old icon if exists
                        old_icon_filename = coin.icon.split('/')[-1]
                        image_processor.delete_from_s3(bucket=S3_BUCKET_ICONS, image_url=old_icon_filename)

                    alias = coin.alias
                    normalized_alias = alias.strip().lower().replace(" ", "")
                    new_icon_filename = secure_filename(f"{normalized_alias}.svg")
                    icon_url = image_processor.upload_svg_to_s3(icon_file, S3_BUCKET_ICONS, new_icon_filename)
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
@cache_with_redis(expiration=21600)
def get_all_coins():
    """
    Retrieve all coins from the database with optional ordering and full details.

    This endpoint fetches all coin bots from the database and returns them as a list
    with full details, including related entities.

    Query Parameters:
        order (str, optional): The order of the returned coins. 
                               Accepts 'asc' or 'desc'. Defaults to 'asc'.

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - coins (list): A list of dictionaries, each representing a coin bot with full details
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Successfully retrieved coins (even if the list is empty)
            - 400: Bad request (invalid order parameter)
            - 500: Internal server error
    """
    response = {
        "success": False,
        "coins": [],
        "error": None
    }
    status_code = 500

    try:
        order = request.args.get('order', 'asc').lower()
        if order not in ['asc', 'desc']:
            response["error"] = "Invalid order argument. Use 'asc' or 'desc'."
            return jsonify(response), 400

        with Session() as session:
            query = session.query(CoinBot)

            if order == 'desc':
                query = query.order_by(CoinBot.name.desc())
            else:
                query = query.order_by(CoinBot.name.asc())
            
            coins = query.all()
            
            response["coins"] = [coin.as_dict() for coin in coins]
            response["success"] = True
            status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code


@coin_bp.route('/coin/<int:coin_id>', methods=['DELETE'])
@update_cache_with_redis(related_get_endpoints=['get_all_coins', 'get_single_coin'])
def delete_coin(coin_id):
    """
    Delete a coin from the database.

    This endpoint removes a coin and its associated icon from the system.
    If the coin has an icon, it will be deleted from the S3 bucket as well.

    Args:
        coin_id (int): The ID of the coin to delete.

    Returns:
        tuple: A tuple containing:
            - A JSON response with the following keys:
                - success (bool): Indicates if the deletion was successful.
                - error (str): Error message if any error occurred, otherwise None.
            - An HTTP status code.

    Raises:
        SQLAlchemyError: If a database error occurs.
        Exception: For any other unexpected errors, including S3 deletion errors.

    Status Codes:
        200: Success
        404: Coin not found
        500: Server error (database error, S3 deletion error, or unexpected error)
    """
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


@coin_bp.route('/coin/<int:coin_id>/toggle-coin', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_coins', 'get_single_coin'])
def toggle_coin_publication(coin_id):
    """
    Toggle the publication status of a coin.

    This endpoint allows for activating or deactivating a coin based on its current status.
    When activating, it checks if the coin's fundamentals are complete and if the chart
    has valid support and resistance lines.

    Args:
        coin_id (int): The ID of the coin to toggle.

    Returns:
        tuple: A tuple containing:
            - A JSON response with the following keys:
                - success (bool): Indicates if the operation was successful.
                - message (str): A descriptive message about the operation result.
                - is_active (bool): The new active status of the coin.
                - error (str): Error message if any error occurred, otherwise None.
            - An HTTP status code.

    Raises:
        SQLAlchemyError: If a database error occurs.
        Exception: For any other unexpected errors.

    Status Codes:
        200: Success
        400: Bad Request (e.g., incomplete fundamentals or invalid chart)
        404: Coin not found
        500: Server error
    """
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
                valid, messages = validate_coin(coin=coin)
                if valid:
                    coin.is_active = True
                    coin.updated_at = datetime.now()
                    session.commit()
                    response["success"] = True
                    response["message"] = "Coin activated successfully"
                    response["is_active"] = True
                    status_code = 200
                else:
                    response["error"] = ', '.join(messages)
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


@coin_bp.route('/coins-ids/<category_name>', methods=['GET'])
@cache_with_redis(expiration=21600)
def get_coins_ids(category_name):
    """
    Retrieve coins IDs associated with a given category name.

    This endpoint queries the database for all coins instances associated with the specified category
    and returns their coin IDs.

    Args:
        category_name (str): The name of the category to find bots for.

    Returns:
        Tuple[Dict, int]: A tuple containing:
            - Dict: JSON response with the following structure:
                {
                    "data": {"coin_ids": List[int]} or None,
                    "error": str or None,
                    "success": bool
                }
            - int: HTTP status code
                - 200: List of bot IDs retrieved successfully
                - 404: Category not found
                - 500: Internal server error

    Raises:
        SQLAlchemyError: If there's an issue with the database query.
        Exception: For any other unexpected errors.

    Note:
        This function uses a SQLAlchemy session to query the database. The session is always
        closed at the end of the function execution, even if an exception occurs.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 500  # Default to server error

    session = Session()
    try:
        category = session.query(Category).filter_by(name=category_name).first()
        if not category:
            response["error"] = 'Category not found'
            status_code = 404
            return jsonify(response), status_code

        # Fetch all coins associated with the category
        coins = session.query(CoinBot).filter_by(category_id=category.category_id).all()
        coin_ids = [coin.bot_id for coin in coins]

        response["data"] = {'coin_ids': coin_ids}
        response["success"] = True
        status_code = 200

    except Exception as e:
        response["error"] = f'Error retrieving coins for category "{category_name}": {str(e)}'
        status_code = 500

    finally:
        session.close()

    return jsonify(response), status_code