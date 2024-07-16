from config import Keyword, Session
from config import Session as DBSession 
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify
from http import HTTPStatus

all_keywords = Blueprint('getAllKeywords', __name__)

@all_keywords.route('/get_keywords_for_coin_bot/<int:coin_bot_id>', methods=['GET'])
def get_keywords_for_coin_bot(coin_bot_id):
    try:
        with DBSession() as db_session:
            keywords = db_session.query(Keyword).filter_by(coin_bot_id=coin_bot_id).all()
            keywords_data = [{'id': keyword.keyword_id, 'word': keyword.word} for keyword in keywords]
            return jsonify({'success': True, 'keywords': keywords_data}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
# ____________________ IMPROVED VERSION ________________________________________

@all_keywords.route('/get_keywords/<int:coin_bot_id>', methods=['GET'])
def get_keywords(coin_bot_id):
    """
    Retrieve all keywords associated with a specific coin bot.

    This endpoint fetches all keywords linked to the given coin_bot_id.

    Args:
        coin_bot_id (int): The ID of the coin bot.

    Returns:
        dict: A JSON response containing either the keywords or an error message.
            Format: {"message": list or None, "error": str or None, "status": int}

    Raises:
        SQLAlchemyError: If there's a database-related error.
    """
    response = {
        "data": None,
        "error": None,
        "status": HTTPStatus.OK
    }

    session = Session()

    try:
        keywords = session.query(Keyword).filter_by(coin_bot_id=coin_bot_id).all()
        
        if keywords:
            keywords_data = [keyword.as_dict() for keyword in keywords]
            response["data"] = keywords_data
        else:
            response["error"] = f"No keywords found for coin bot ID: {coin_bot_id}"
            response["status"] = HTTPStatus.NOT_FOUND

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

    return jsonify(response), response["status"]