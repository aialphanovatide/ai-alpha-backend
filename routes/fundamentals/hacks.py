from flask import Blueprint, jsonify, request
from config import Session, session, CoinBot
from config import Hacks

hacks_bp = Blueprint('hacksRoutes', __name__)

@hacks_bp.route('/api/hacks', methods=['GET'])
def get_hacks():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        coin_bot_name = request.args.get('coin_bot_name')

        if coin_bot_name is None and coin_bot_id is None:
            return jsonify({'message': 'Coin ID or name is missing', 'status': 400}), 400

        coin_data = None

        if coin_bot_name:
            coin = session.query(CoinBot).filter(CoinBot.bot_name==coin_bot_name).first()
            coin_data = session.query(Hacks).filter_by(coin_bot_id=coin.bot_id).all()

        if coin_bot_id:
            coin_data = session.query(Hacks).filter_by(coin_bot_id=coin_bot_id).all()
        
        if coin_data is None:
            return {'message': 'No hacks found for the requested coin', 'status': 404}, 404

        hacks_list = [hack.as_dict() for hack in coin_data]
        return jsonify({'message': hacks_list}), 200
    except Exception as e:
        return jsonify({'error': f'Error getting hacks data: {str(e)}', 'status': 500}), 500
    

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
    
    
@hacks_bp.route('/api/hacks/edit/<int:hack_id>', methods=['PUT'])
def edit_hack(hack_id):
    try:
        data = request.json
        hack_to_edit = session.query(Hacks).filter(Hacks.id == hack_id).first()

        if not hack_to_edit:
            return {'message': 'Hack not found', 'status': 404}, 404

        # Actualizar los campos del hack con los datos recibidos en el body de la solicitud
        hack_to_edit.hack_name = data.get('hackName', hack_to_edit.hack_name)
        hack_to_edit.date = data.get('date', hack_to_edit.date)
        hack_to_edit.incident_description = data.get('incidentDescription', hack_to_edit.incident_description)
        hack_to_edit.consequences = data.get('consequences', hack_to_edit.consequences)
        hack_to_edit.mitigation_measure = data.get('mitigationMeasure', hack_to_edit.mitigation_measure)

        session.commit()

        return {'message': f'Hack with ID {hack_id} updated successfully', 'status': 200}, 200
    except Exception as e:
        return {'error': f'Error editing hack: {str(e)}', 'status': 500}, 500
