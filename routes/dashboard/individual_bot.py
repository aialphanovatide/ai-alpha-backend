from flask import Blueprint, jsonify
from routes.news_bot.index import activate_news_bot, deactivate_news_bot

individual_bot = Blueprint('individualBot', __name__)

@individual_bot.route('/activate_bot_by_id/<category_name>', methods=['POST'])
def activate_bot_by_id(category_name):
    try:
        message, status_code = activate_news_bot(category_name)
        return jsonify({"message": message}), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@individual_bot.route('/deactivate_bot_by_id/<category_name>', methods=['POST'])
def deactivate_bot_by_id(category_name):
    try:
        message, status_code = deactivate_news_bot(category_name)
        return jsonify({"message": message}), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
