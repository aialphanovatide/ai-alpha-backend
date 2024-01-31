from flask import Blueprint
from config import Category
from routes.news_bot.index import deactivate_news_bot
from flask import jsonify
from config import Session as DBSession 

bots_deactivator = Blueprint('bots_deactivator', __name__)


@bots_deactivator.route('/deactivate_all_bots', methods=['POST'])
def deactivate_bot():
    try:
        with DBSession() as db_session:
            categories = db_session.query(Category).all()

        for category in categories:
            deactivate_news_bot(category.category)

        any_inactive = any(not category.is_active for category in categories)
        return jsonify({"bots": [{"category": category.category, "isActive": category.is_active} for category in categories], "any_inactive": any_inactive})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
