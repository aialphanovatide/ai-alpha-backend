from config import Category
from flask import jsonify
from config import Session as DBSession 
from flask import Blueprint

bots_status = Blueprint('get_bots_status', __name__)

@bots_status.route('/get_bot_status')
def get_bot_status():
    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    bot_statuses = {category.category: category.is_active for category in categories}
    print(bot_statuses)
    return jsonify({'success': True, 'bot_statuses': bot_statuses})