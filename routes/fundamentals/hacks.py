from flask import Blueprint, jsonify, request
from config import Session, session
from config import Hacks

hacks_bp = Blueprint('hacksRoutes', __name__)

@hacks_bp.route('/api/hacks', methods=['GET'])
def get_hacks():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        hacks_data = session.query(Hacks).filter_by(coin_bot_id=coin_bot_id).all()
        if not hacks_data:
            return {'error': 'No data found for the requested coin'}, 404

        hacks_list = [hack.as_dict() for hack in hacks_data]
        return jsonify({'message': hacks_list}), 200
    except Exception as e:
        return {'error': f'Error getting hacks data: {str(e)}'}, 500

@hacks_bp.route('/api/hacks/create', methods=['POST'])
def create_hack():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')
        new_hack = Hacks(
            hack_name=data.get('hackName'),
            date=data.get('date'),
            incident_description=data.get('incidentDescription'),
            consequences=data.get('consequences'),
            mitigation_measure=data.get('mitigationMeasure'),
            coin_bot_id=coin_bot_id
        )
        
        session = Session()
        session.add(new_hack)
        session.commit()

        return {'message': f'Hack for coin_bot_id {coin_bot_id} created successfully'}, 201
    except Exception as e:
        return {'error': f'Error creating hack: {str(e)}'}, 500