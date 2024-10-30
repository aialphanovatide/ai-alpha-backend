import os
from flask import jsonify, Blueprint, request
from config import Category, Chart, CoinBot, Session
from services.aws.s3 import ImageProcessor
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from redis_client.redis_client import cache_with_redis, update_cache_with_redis
from werkzeug.exceptions import BadRequest
from sqlalchemy import func, asc, desc


category_bp = Blueprint('category_bp', __name__)

S3_BUCKET_ICONS = os.getenv('S3_BUCKET_ICONS')

# Initialize the ImageProcessor
image_processor = ImageProcessor()

@category_bp.route('/category', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_categories'])
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
            - 400: Bad request (missing required fields, invalid SVG, or category already exists)
            - 500: Internal server error
    """
    response = {
        "success": False,
        "category": None,
        "error": None
    }
    status_code = 500
    with Session() as session:
        try:
            name = request.form.get('name')
            alias = request.form.get('alias')
            border_color = request.form.get('border_color')
            icon_file = request.files.get('icon')

            if not name or not alias:
                response["error"] = 'Name and Alias are required and cannot be null'
                status_code = 400
                return jsonify(response), status_code

            # Check if category with same name or alias already exists
            existing_category = session.query(Category).filter(
                (func.lower(Category.name) == func.lower(name)) |
                (func.lower(Category.alias) == func.lower(alias))
            ).first()

            if existing_category:
                if existing_category.name.lower() == name.lower():
                    response["error"] = f'A category with the name "{name}" already exists'
                else:
                    response["error"] = f'A category with the alias "{alias}" already exists'
                status_code = 400
                return jsonify(response), status_code

            icon_url = None
            if icon_file:
                normalized_alias = alias.strip().lower().replace(" ", "")
                icon_filename = secure_filename(f"{normalized_alias}.svg")
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


@category_bp.route('/category/<int:category_id>', methods=['GET'])
@cache_with_redis(expiration=21600)
def get_single_category(category_id):
    """
    Retrieve a single category with its associated coins.

    This endpoint fetches a specific category from the database and returns it
    with full details, including all associated coins.

    Args:
        category_id (int): The ID of the category to retrieve.

    Query Parameters:
        order (str, optional): The order of the returned coins within the category. 
                               Accepts 'asc' or 'desc'. Defaults to 'asc'.

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - category (dict or None): A dictionary representing the category with full details,
                                       including a list of associated coins
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Successfully retrieved the category
            - 400: Bad request (invalid order parameter)
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
        order = request.args.get('order', 'asc').lower()
        if order not in ['asc', 'desc']:
            response["error"] = "Invalid order argument. Use 'asc' or 'desc'."
            return jsonify(response), 400

        with Session() as session:
            category = session.query(Category).options(
                joinedload(Category.coin_bot)
            ).get(category_id)

            if not category:
                response["error"] = f"Category with ID {category_id} not found"
                return jsonify(response), 404

            category_dict = category.as_dict()
            
            # Order coins within the category
            if order == 'desc':
                ordered_coins = sorted(category.coin_bot, key=lambda x: (x.name is None, x.name or ''), reverse=True)
            else:
                ordered_coins = sorted(category.coin_bot, key=lambda x: (x.name is None, x.name or ''))
            
            category_dict['coins'] = [coin.as_dict() for coin in ordered_coins]

            response["category"] = category_dict
            response["success"] = True
            status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code


@category_bp.route('/categories', methods=['GET'])
@cache_with_redis(expiration=21600)
def get_all_categories():
    """
    Retrieve all categories with their associated CoinBots, sorted alphabetically by name.

    This endpoint fetches all categories from the database, orders them alphabetically by name,
    and includes their associated CoinBots.

    Query Parameters:
        order (str, optional): The order of the returned categories. 
                               Accepts 'asc' or 'desc'. Defaults to 'asc'.

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - categories (list): A list of dictionaries, each representing a category with its CoinBots
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Successfully retrieved categories
            - 400: Bad request (invalid order parameter)
            - 500: Internal server error
    """
    response = {
        "success": False,
        "categories": [],
        "error": None
    }
    status_code = 500

    try:
        order = request.args.get('order', 'asc').lower()
        if order not in ['asc', 'desc']:
            response["error"] = "Invalid order argument. Use 'asc' or 'desc'."
            return jsonify(response), 400

        with Session() as session:
            query = session.query(Category).options(
                joinedload(Category.coin_bot)
            )

            if order == 'desc':
                query = query.order_by(desc(Category.name))
            else:
                query = query.order_by(asc(Category.name))
            
            categories = query.all()
            
            for category in categories:
                category_dict = category.as_dict()
                # Order coins within each category, handling potential None or falsy names
                if order == 'desc':
                    ordered_coins = sorted(category.coin_bot, key=lambda x: (x.name is None, x.name or ''), reverse=True)
                else:
                    ordered_coins = sorted(category.coin_bot, key=lambda x: (x.name is None, x.name or ''))
                category_dict['coins'] = [coin.as_dict() for coin in ordered_coins]
                response["categories"].append(category_dict)

            response["success"] = True
            status_code = 200

    except SQLAlchemyError as e:
        response["error"] = f"Database error occurred: {str(e)}"
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code
    
    
@category_bp.route('/category/<int:category_id>', methods=['DELETE'])
@update_cache_with_redis(related_get_endpoints=['get_all_categories', 'get_single_category'])
def delete_category(category_id):
    """
    Delete a category and its associated icon from the database and S3 storage.

    This endpoint removes a specific category from the database, identified by its category_id.
    If the category has an associated icon, it is also deleted from the S3 storage.

    Args:
        category_id (int): The ID of the category to be deleted.

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - error (str or None): Error message, if any
        HTTP Status Code:
            - 200: Successfully deleted the category
            - 404: Category not found
            - 500: Internal server error

    Raises:
        SQLAlchemyError: If a database error occurs during the deletion process.
        Exception: For any other unexpected errors.
    """
    response = {
        "success": False,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            # Find the category to delete
            category = session.query(Category).get(category_id)

            if not category:
                response["error"] = f"No category found with ID: {category_id}"
                return jsonify(response), 404

            # Delete associated icon from S3
            if category.icon:
                icon_filename = category.icon
                image_processor.delete_from_s3(S3_BUCKET_ICONS, icon_filename)

            # Delete the category from the database
            session.delete(category)
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


@category_bp.route('/category/<int:category_id>', methods=['PUT'])
@update_cache_with_redis(related_get_endpoints=['get_all_categories', 'get_single_category'])
def update_category(category_id):
    """
    Update a category's information in the database.

    This function handles PUT requests to update the details of a specific category,
    identified by its category_id. It can update various fields including name, alias,
    border color, and icon.

    Args:
        category_id (int): The ID of the category to be updated.

    Returns:
        tuple: A tuple containing:
            - A JSON response with the following structure:
                {
                    "success": bool,
                    "category": dict or None,
                    "error": str or None
                }
            - An HTTP status code (int)

    Raises:
        BadRequest: If no update data is provided.
        ValueError: If there's an error processing the icon.
        IntegrityError: If there's a database integrity violation.
        SQLAlchemyError: If a database error occurs.
        Exception: For any other unexpected errors.

    Note:
        This function interacts with the database using SQLAlchemy sessions and
        handles file operations for icon updates using S3 bucket storage.
    """
    response = {
        "success": False,
        "category": None,
        "error": None
    }
    status_code = 500

    with Session() as session:
        try:
            data = request.form
            icon_file = request.files.get('icon')
            if not data and not icon_file:
                raise BadRequest('No update data provided')

            category = session.query(Category).get(category_id)
            if not category:
                response["error"] = f'Category with ID {category_id} not found'
                return jsonify(response), 404

            # Update fields if provided
            for field in ['name', 'alias', 'border_color']:
                if field in data:
                    setattr(category, field, data[field])

            if icon_file:
                try:
                    if category.icon:  # Delete old icon if exists
                        old_icon_filename = category.icon.split('/')[-1]
                        image_processor.delete_from_s3(bucket=S3_BUCKET_ICONS, image_url=old_icon_filename)

                    alias = category.alias or category.name
                    normalized_alias = alias.strip().lower().replace(" ", "")
                    new_icon_filename = secure_filename(f"{normalized_alias}.svg")
                    icon_url = image_processor.upload_svg_to_s3(icon_file, S3_BUCKET_ICONS, new_icon_filename)
                    if not icon_url:
                        raise ValueError('Failed to upload new SVG icon')
                    category.icon = icon_url
                except Exception as e:
                    raise ValueError(f"Error processing icon: {str(e)}")

            session.commit()
            response["success"] = True
            response["category"] = category.as_dict()
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


@category_bp.route('/categories/<int:category_id>/toggle-coins', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_categories', 'get_single_category'])
def toggle_category_coins(category_id):
    """
    Activate or deactivate all coins within a specific category.

    Args:
        category_id (int): The ID of the category to process.

    Request JSON:
        action (str): Either "activate" or "deactivate"

    Returns:
        JSON: A response detailing the status of each processed coin bot and the category.
        HTTP Status Code:
            - 200: Successfully processed the request
            - 400: Invalid action provided
            - 404: Category not found
            - 500: Internal server error
    """
    response = {
        "success": False,
        "processed_coins": [],
        "category_status": "",
        "error": None
    }

    # Get action from the request
    action = request.json.get('action')
    if action not in ['activate', 'deactivate']:
        response["error"] = 'Invalid action. Must be "activate" or "deactivate".'
        return jsonify(response), 400

    with Session() as session:
        try:
            # Fetch the category by ID
            category = session.query(Category).get(category_id)
            if not category:
                response["error"] = f'Category with ID {category_id} not found.'
                return jsonify(response), 404

            # Fetch all coins in the category
            coins = session.query(CoinBot).filter_by(category_id=category_id).all()

            if not coins:
                response["error"] = f'No coins found for category with ID {category_id}.'
                return jsonify(response), 404

            all_valid = True

            for coin in coins:
                coin_status = {
                    "id": coin.bot_id,
                    "name": coin.name,
                    "status": "unchanged",
                    "message": ""
                }

                # Handle activation of the coin
                if action == "activate":
                    valid, messages = validate_coin(coin)

                    if valid:
                        coin_status["status"] = "activated"
                        coin_status["message"] = "coin activated"
                        coin.is_active = True
                    else:
                        coin_status["status"] = "invalid"
                        coin_status["message"] = ', '.join(messages)
                        all_valid = False

                # Handle deactivation of the coin
                elif action == "deactivate":
                    coin_status["status"] = "deactivated"
                    coin_status["message"] = "coin deactivated"
                    coin.is_active = False

                response["processed_coins"].append(coin_status)

            # Update category status based on the action and validation results
            if action == "activate":
                if all_valid:
                    category.is_active = True
                    response["category_status"] = "activated"
                else:
                    response["category_status"] = "Not all coins were activated"
            elif action == "deactivate":
                category.is_active = False
                response["category_status"] = "deactivated"

            # Commit the changes to the database
            session.commit()
            response["success"] = True
            return jsonify(response), 200

        except SQLAlchemyError as e:
            # Handle SQL errors, rollback changes if necessary
            session.rollback()
            response["error"] = f"Database error occurred: {str(e)}"
            return jsonify(response), 500

        except Exception as e:
            # Handle unexpected errors
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            return jsonify(response), 500
    

@category_bp.route('/categories/global-toggle', methods=['POST'])
@update_cache_with_redis(related_get_endpoints=['get_all_categories', 'get_single_category'])
def global_toggle_coins():
    """
    Activate or deactivate all coins across all categories.

    Request JSON:
        action (str): Either "activate" or "deactivate"

    Returns:
        JSON: A response detailing the status of each processed category and its coin bots.
        HTTP Status Code:
            - 200: Successfully processed the request
            - 400: Invalid action provided
            - 404: No categories or coins found
            - 500: Internal server error
    """
    response = {
        "success": False,
        "processed_categories": [],
        "error": None
    }

    action = request.json.get('action')
    if action not in ['activate', 'deactivate']:
        response["error"] = 'Invalid action. Must be "activate" or "deactivate".'
        return jsonify(response), 400

    with Session() as session:
        try:
            categories = session.query(Category).options(joinedload(Category.coin_bot)).all()

            if not categories:
                response["error"] = 'No categories found.'
                return jsonify(response), 404

            for category in categories:
                category_result = {
                    'category_id': category.category_id,
                    'name': category.name,
                    'status': 'unchanged',
                    'processed_coin_bots': []
                }

                if not category.coin_bot:
                    category_result['status'] = 'skipped'
                    category_result['message'] = 'No coin bots found in this category'
                    response['processed_categories'].append(category_result)
                    continue

                all_valid = True

                for coin_bot in category.coin_bot:
                    bot_result = {
                        'bot_id': coin_bot.bot_id,
                        'name': coin_bot.name,
                        'status': 'unchanged',
                        'message': ''
                    }

                    if action == 'activate':
                        valid, messages = validate_coin(coin_bot)
                        if valid:
                            coin_bot.is_active = True
                            bot_result['status'] = 'activated'
                            bot_result['message'] = 'Coin bot activated'
                        else:
                            bot_result['status'] = 'invalid'
                            bot_result['message'] = ', '.join(messages)
                            all_valid = False
                    else:  # deactivate
                        coin_bot.is_active = False
                        bot_result['status'] = 'deactivated'
                        bot_result['message'] = 'Coin bot deactivated'

                    category_result['processed_coin_bots'].append(bot_result)

                if action == 'activate':
                    if all_valid:
                        category.is_active = True
                        category_result['status'] = 'activated'
                    else:
                        category_result['status'] = 'partially activated'
                        category_result['message'] = 'Not all coin bots were activated'
                elif action == 'deactivate':
                    category.is_active = False
                    category_result['status'] = 'deactivated'

                response['processed_categories'].append(category_result)

            session.commit()
            response["success"] = True
            return jsonify(response), 200

        except SQLAlchemyError as e:
            session.rollback()
            response["error"] = f"Database error occurred: {str(e)}"
            return jsonify(response), 500

        except Exception as e:
            session.rollback()
            response["error"] = f"An unexpected error occurred: {str(e)}"
            return jsonify(response), 500


def validate_coin(coin, session=None):
    """Validate if a coin bot meets all requirements for activation."""
    error_messages = []
    should_close_session = False
    
    if session is None:
        session = Session()
        should_close_session = True
    
    try:
        print(f"[DEBUG] Starting validation for coin: {coin.name} (ID: {coin.bot_id})")
        
        if not session.is_active or coin not in session:
            print("[DEBUG] Merging coin with session")
            coin = session.merge(coin)
        
        print("[DEBUG] Refreshing coin relationships")
        session.refresh(coin)
        
        print("[DEBUG] Checking fundamentals")
        fundamentals_complete, missing_fundamentals = are_coin_fundamentals_complete(coin)
        if not fundamentals_complete:
            error_messages.append(f"Missing fundamentals: {', '.join(missing_fundamentals)}")
        
        print("[DEBUG] Checking chart")
        chart = session.query(Chart).filter_by(coin_bot_id=coin.bot_id).first()
        print(f"[DEBUG] Chart exists: {bool(chart)}")
        if not chart:
            error_messages.append("Chart is missing - Check support and resistance lines")
        elif not has_support_resistance_lines(chart):
            error_messages.append("Support and Resistance lines are incomplete")

        print(f"[DEBUG] Validation complete. Errors: {error_messages}")
        return (not bool(error_messages), error_messages or ['Valid coin'])
        
    except Exception as e:
        print(f"[DEBUG] Exception in validate_coin: {str(e)}")
        raise
    finally:
        if should_close_session:
            session.close()

def are_coin_fundamentals_complete(coin):
    """Check if all required fundamental sections are complete."""
    print(f"[DEBUG] Checking fundamentals for coin: {coin.name} (ID: {coin.bot_id})")
    missing_fundamentals = []
    
    # Check introduction
    introduction = coin.introduction[0] if coin.introduction else None
    if not introduction or not introduction.content:
        missing_fundamentals.append("Introduction")
    
    # Check tokenomics
    tokenomics = coin.tokenomics[0] if coin.tokenomics else None
    if not tokenomics or not (tokenomics.token and tokenomics.total_supply):
        missing_fundamentals.append("Tokenomics")
    
    # Check token distribution
    if not any(td.holder_category and td.percentage_held for td in coin.token_distribution):
        missing_fundamentals.append("Token Distribution")
    
    # Check token utility
    if not any(tu.token_application and tu.description for tu in coin.token_utility):
        missing_fundamentals.append("Token Utility")
    
    # Check value accrual
    if not any(vam.mechanism and vam.description for vam in coin.value_accrual_mechanisms):
        missing_fundamentals.append("Value Accrual Mechanisms")
    
    # Check competitors
    if not any(comp.name for comp in coin.competitor):
        missing_fundamentals.append("Competitors")
    
    # Check revenue model
    revenue_model = coin.revenue_model[0] if coin.revenue_model else None
    if not revenue_model or not revenue_model.analized_revenue:
        missing_fundamentals.append("Revenue Model")

    print(f"[DEBUG] Missing fundamentals: {missing_fundamentals}")
    
    # Return True only if no fundamentals are missing
    return len(missing_fundamentals) == 0, missing_fundamentals

def has_support_resistance_lines(chart):
    """
    Check if the chart has all 8 support and resistance lines with values.
    
    Args:
        chart (Chart): The Chart object to check.

    Returns:
        bool: True if the chart has all 8 support and resistance lines with values, False otherwise.
    """
    support_lines = [chart.support_1, chart.support_2, chart.support_3, chart.support_4]
    resistance_lines = [chart.resistance_1, chart.resistance_2, chart.resistance_3, chart.resistance_4]
    
    all_lines_present = all(support_lines) and all(resistance_lines)
    
    return all_lines_present

            

# def validate_coin(coin, session=None):
#     """
#     Validate if a coin bot meets all requirements for activation.
    
#     Args:
#         coin_bot (CoinBot): The CoinBot object to validate.
#         session (Session, optional): SQLAlchemy session to use. If None, creates new session.

#     Returns:
#         tuple: (bool, list) Validation result and list of messages.
#     """
#     error_messages = []
    
#     # Use provided session or create new one
#     should_close_session = False
#     if session is None:
#         session = Session()
#         should_close_session = True
        
#     try:
#         # Merge the coin object with the current session if it came from another
#         if not session.is_active or coin not in session:
#             coin = session.merge(coin)
            
#         # Check if fundamentals exist and are complete
#         if not are_coin_fundamentals_complete(coin):
#             error_messages.append('Fundamentals are incomplete')
        
#         # Check if chart exists and has support and resistance lines
#         chart = session.query(Chart).filter_by(coin_bot_id=coin.bot_id).first()
#         if not chart or not has_support_resistance_lines(chart):
#             error_messages.append('S&R Lines are incomplete')

#         # If there are any error messages, validation failed
#         if error_messages:
#             return False, error_messages

#         # If no error messages, validation passed
#         return True, ['Valid coin']
        
#     finally:
#         if should_close_session:
#             session.close()



# def are_coin_fundamentals_complete(coin):
#     """
#     Check if all required fundamental sections are complete for a given CoinBot.
    
#     This function verifies that the CoinBot has the necessary content in each of
#     the fundamental sections considered essential for the coin's information.

#     Args:
#         coin (CoinBot): The CoinBot object to check.

#     Returns:
#         bool: True if all fundamental sections are complete, False otherwise.
#     """
#     # Check if each fundamental section exists and has content
#     has_introduction = coin.introduction and coin.introduction.content
#     has_tokenomics = coin.tokenomics and coin.tokenomics.token and coin.tokenomics.total_supply
#     has_token_distribution = any(td.holder_category and td.percentage_held for td in coin.token_distribution)
#     has_token_utility = any(tu.token_application and tu.description for tu in coin.token_utility)
#     has_value_accrual = any(vam.mechanism and vam.description for vam in coin.value_accrual_mechanisms)
#     has_competitor = any(comp.name for comp in coin.competitor)
#     has_revenue_model = coin.revenue_model and coin.revenue_model.analized_revenue

#     return all([
#         has_introduction,
#         has_tokenomics,
#         has_token_distribution,
#         has_token_utility,
#         has_value_accrual,
#         has_competitor,
#         has_revenue_model
#     ])


# def validate_coin(coin):
#     """
#     Validate if a coin bot meets all requirements for activation.
    
#     Args:
#         coin_bot (CoinBot): The CoinBot object to validate.

#     Returns:
#         bool: True if the coin bot passes all validations, False otherwise.
#     """
#     error_messages = []

#     with Session() as session:
#         # Refresh the coin object to ensure all relationships are loaded
#         session.refresh(coin)
#         # Check if fundamentals exist and are complete
#         if not coin or not are_coin_fundamentals_complete(coin):
#             error_messages.append('Fundamentals are incomplete')
        
#         # Check if chart exists and has support and resistance lines
#         chart = session.query(Chart).filter_by(coin_bot_id=coin.bot_id).first()
#         if not chart or not has_support_resistance_lines(chart):
#             error_messages.append('S&R Lines are incomplete')

#     # If there are any error messages, validation failed
#     if error_messages:
#         return False, error_messages

#     # If no error messages, validation passed
#     return True, ['Valid coin']