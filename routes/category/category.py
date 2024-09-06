import os
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from config import Category, Chart, CoinBot, session
from services.aws.s3 import ImageProcessor
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

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




@category_bp.route('/categories/<int:category_id>/toggle-coins', methods=['POST'])
def toggle_category_coins(category_id):
    """
    Activate or deactivate all coins within a specific category.

    Args:
        category_id (int): The ID of the category to process.

    Request JSON:
        action (str): Either "activate" or "deactivate"

    Returns:
        JSON: A response detailing the status of each processed coin bot and the category.
    """
    action = request.json.get('action')
    if action not in ['activate', 'deactivate']:
        return jsonify({'error': 'Invalid action. Must be "activate" or "deactivate"'}), 400

    try:
        category = session.query(Category).get(category_id)
        if not category:
            return jsonify({'error': f'Category with ID {category_id} not found'}), 404

        coin_bots = session.query(CoinBot).filter_by(category_id=category_id).all()
        response = {'success': True, 'processed_coin_bots': [], 'category_status': ''}

        all_valid = True
        for coin_bot in coin_bots:
            result = {
                'bot_id': coin_bot.bot_id,
                'bot_name': coin_bot.bot_name,
                'status': 'unchanged',
                'message': ''
            }

            if action == 'activate':
                if validate_coin_bot(coin_bot):
                    result['status'] = 'valid'
                else:
                    result['status'] = 'invalid'
                    result['message'] = 'Failed validation'
                    all_valid = False
            else:  # deactivate
                result['status'] = 'deactivated'

            response['processed_coin_bots'].append(result)

        if action == 'activate' and all_valid:
            category.is_active = True
            response['category_status'] = 'activated'
        elif action == 'deactivate':
            category.is_active = False
            response['category_status'] = 'deactivated'
        else:
            response['category_status'] = 'unchanged'
            response['message'] = 'Not all coin bots passed validation'

        session.commit()
        return jsonify(response), 200

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    

@category_bp.route('/coins/global-toggle', methods=['POST'])
def global_toggle_coins():
    """
    Activate or deactivate all coins across all categories.

    Request JSON:
        action (str): Either "activate" or "deactivate"

    Returns:
        JSON: A response detailing the status of each processed category and its coin bots.
    """
    action = request.json.get('action')
    if action not in ['activate', 'deactivate']:
        return jsonify({'error': 'Invalid action. Must be "activate" or "deactivate"'}), 400

    try:
        categories = session.query(Category).options(joinedload(Category.coin_bot)).all()
        response = {'success': True, 'processed_categories': []}

        for category in categories:
            category_result = {
                'category_id': category.category_id,
                'name': category.name,
                'status': 'unchanged',
                'processed_coin_bots': []
            }

            all_valid = True
            for coin_bot in category.coin_bot:
                bot_result = {
                    'bot_id': coin_bot.bot_id,
                    'bot_name': coin_bot.bot_name,
                    'status': 'unchanged',
                    'message': ''
                }

                if action == 'activate':
                    if validate_coin_bot(coin_bot):
                        coin_bot.is_active = True
                        bot_result['status'] = 'activated'
                    else:
                        bot_result['status'] = 'invalid'
                        bot_result['message'] = 'Failed validation'
                        all_valid = False
                else:  # deactivate
                    coin_bot.is_active = False
                    bot_result['status'] = 'deactivated'

                category_result['processed_coin_bots'].append(bot_result)

            if action == 'activate' and all_valid:
                category.is_active = True
                category_result['status'] = 'activated'
            elif action == 'deactivate':
                category.is_active = False
                category_result['status'] = 'deactivated'
            else:
                category_result['status'] = 'unchanged'
                category_result['message'] = 'Not all coin bots passed validation'

            response['processed_categories'].append(category_result)

        session.commit()
        return jsonify(response), 200

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

def validate_coin_bot(coin_bot):
    """
    Validate if a coin bot meets all requirements for activation.
    
    Args:
        coin_bot (CoinBot): The CoinBot object to validate.

    Returns:
        bool: True if the coin bot passes all validations, False otherwise.
    """
    # Check if fundamentals exist and are complete
    fundamentals = session.query(fundamentals).filter_by(bot_id=coin_bot.bot_id).first()
    if not fundamentals or not are_fundamentals_complete(fundamentals):
        return False

    # Check if chart exists and has support and resistance lines
    chart = session.query(Chart).filter_by(bot_id=coin_bot.bot_id).first()
    if not chart or not has_support_resistance_lines(chart):
        return False

    return True

def are_fundamentals_complete(coin_bot):
    """
    Check if all required sections of fundamentals are complete for a given CoinBot.
    
    Args:
        coin_bot (CoinBot): The CoinBot object to check.

    Returns:
        bool: True if all fundamental sections are complete, False otherwise.
    """
    # Check if each fundamental section exists and has content
    has_introduction = coin_bot.introduction and coin_bot.introduction.content
    has_tokenomics = coin_bot.tokenomics and coin_bot.tokenomics.token and coin_bot.tokenomics.total_supply
    has_token_distribution = any(td.holder_category and td.percentage_held for td in coin_bot.token_distribution)
    has_token_utility = any(tu.token_application and tu.description for tu in coin_bot.token_utility)
    has_value_accrual = any(vam.mechanism and vam.description for vam in coin_bot.value_accrual_mechanisms)
    has_competitor = any(comp.name for comp in coin_bot.competitor)
    has_revenue_model = coin_bot.revenue_model and coin_bot.revenue_model.analized_revenue

    return all([
        has_introduction,
        has_tokenomics,
        has_token_distribution,
        has_token_utility,
        has_value_accrual,
        has_competitor,
        has_revenue_model
    ])

def has_support_resistance_lines(chart):
    """
    Check if the chart has at least one support and one resistance line.
    
    Args:
        chart (Chart): The Chart object to check.

    Returns:
        bool: True if the chart has at least one support and one resistance line, False otherwise.
    """
    has_support = any([chart.support_1, chart.support_2, chart.support_3, chart.support_4])
    has_resistance = any([chart.resistance_1, chart.resistance_2, chart.resistance_3, chart.resistance_4])
    
    return has_support and has_resistance