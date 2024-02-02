from flask import Blueprint, jsonify, request
from config import Session
from config import Hacks

hacks_bp = Blueprint('hacksRoutes', __name__)

@hacks_bp.route('/api/hacks', methods=['GET'])
def get_hacks():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        if coin_bot_id is None or not coin_bot_id.isdigit():
            return {'error': 'Coin is required and must be a non-empty string containing only digits'}, 400

        session = Session()
        hacks_data = session.query(Hacks).filter_by(coin_bot_id=coin_bot_id).all()

        if not hacks_data:
            return {'error': 'No data found for the requested coin'}, 404

        hacks_list = [hack.as_dict() for hack in hacks_data]
        return {'hacks': hacks_list}, 200
    except Exception as e:
        return {'error': f'Error getting hacks data: {str(e)}'}, 500

@hacks_bp.route('/api/hacks/create', methods=['POST'])
def create_hack():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')
        
        new_hack = Hacks(
            hack_name=data.get('hack_name'),
            date=data.get('date'),
            incident_description=data.get('incident_description'),
            consequences=data.get('consequences'),
            mitigation_measure=data.get('mitigation_measure'),
            coin_bot_id=coin_bot_id
        )

        session = Session()
        session.add(new_hack)
        session.commit()

        return {'message': f'Hack for coin_bot_id {coin_bot_id} created successfully'}, 201
    except Exception as e:
        return {'error': f'Error creating hack: {str(e)}'}, 500