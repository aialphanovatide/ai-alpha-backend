from config import Site  
from flask import jsonify
from config import Session as DBSession
from flask import Blueprint

all_sites = Blueprint('getAllSites', __name__)

@all_sites.route('/get_sites_for_coin_bot/<int:coin_bot_id>', methods=['GET'])
def get_sites_for_coin_bot(coin_bot_id):
    print(coin_bot_id)
    try:
        with DBSession() as db_session:
            # Obtener los sitios para el coinBot específico
            sites = db_session.query(Site).filter_by(coin_bot_id=coin_bot_id).all()
            sites_data = [{'id': site.site_id, 'url': site.site_name} for site in sites]
            return jsonify({'success': True, 'sites': sites_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
