from config import Session
from config import Category
from sqlalchemy import desc
from flask import Blueprint, jsonify

getBots = Blueprint('getAllBots', __name__)

@getBots.route('/get_all_bots', methods=['GET'])
def get_bots():
    try:
        with Session() as db_session:
            categories = db_session.query(Category).order_by(Category.category_id).all()
        
        bots = [{'category': category.category, 'isActive': category.is_active, 
                 'alias': category.category_name, 'icon': category.icon, 'color': category.border_color} for category in categories]
        return jsonify({'success': True, 'bots': bots}), 200
    except Exception as e:
        return jsonify({'success': False, 'bots': [], 'error': str(e)}), 500