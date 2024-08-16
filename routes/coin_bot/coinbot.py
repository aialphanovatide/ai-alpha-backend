from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, Blueprint, request
from config import Category, CoinBot, session
from datetime import datetime

coin_bot_bp = Blueprint('coin_bot_bp', __name__)

@coin_bot_bp.route('/create_coin_bot', methods=['POST'])
def create_coin_bot():
    """
    Create a new coin bot in the database.

    This endpoint creates a new coin bot entry with the provided details and
    saves it to the database. It returns the created coin bot data if successful.

    Request JSON:
    {
        "bot_name": str,       # The name of the bot (required)
        "category_id": int,    # The ID of the category (required)
        "image": str           # The image associated with the bot (optional, default: 'No Image')
    }

    Returns:
        JSON: A JSON object containing:
            - success (bool): Indicates if the operation was successful
            - coin_bot (dict or None): The created coin bot data or None
            - error (str or None): Error message, if any
        HTTP Status Code

    Raises:
        400 Bad Request: If required fields are missing
        404 Not Found: If the category ID does not exist
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {
        "success": False,
        "coin_bot": None,
        "error": None
    }
    status_code = 500  # Default to server error

    try:
        data = request.json

        # Extract data from JSON
        bot_name = data.get('bot_name')
        category_id = data.get('category_id')
        image = data.get('image', 'No Image')

        # Validate required fields
        if not bot_name or not category_id:
            response["error"] = 'Bot name and category ID are required'
            status_code = 400
            return jsonify(response), status_code

        # Check if the category exists
        existing_category = session.query(Category).get(category_id)
        if not existing_category:
            response["error"] = 'Category ID not found'
            status_code = 404
            return jsonify(response), status_code

        # Create a new instance of CoinBot
        new_coin_bot = CoinBot(
            bot_name=bot_name,
            category_id=category_id,
            image=image,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Add the coin bot to the database
        session.add(new_coin_bot)
        session.commit()

        response["success"] = True
        response["coin_bot"] = new_coin_bot.as_dict()  # Asegúrate de que CoinBot tenga un método as_dict()
        status_code = 200  # OK

    except SQLAlchemyError as e:
        session.rollback()  # Rollback in case of database error
        response["error"] = f"Database error occurred: {str(e)}"
        status_code = 500
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code