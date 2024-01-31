from config import Category
from flask import jsonify
from config import Session as DBSession 
from flask import Blueprint


total_bots = Blueprint('totalBots', __name__)

@total_bots.route('/get_all_bots', methods=['GET'])
def get_all_bots():

    with DBSession() as db_session:
        categories = db_session.query(Category).all()

    # Transformar la información de las categorías a un formato deseado
    bots = [{'category': category.category, 'isActive': category.is_active} for category in categories]
    

    return jsonify({'success': True, 'bots': bots})