from config import Category
from config import Session as DBSession
from flask import Blueprint, jsonify

getBots = Blueprint('getAllBots', __name__)

@getBots.route('/get_all_bots', methods=['GET'])
def get_bots():
    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    # Transformar la información de las categorías a un formato deseado
    bots = [{'category': category.category, 'isActive': category.is_active} for category in categories]
    
    return jsonify({'success': True, 'bots': bots})