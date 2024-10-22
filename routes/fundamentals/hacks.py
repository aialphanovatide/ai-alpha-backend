from flask import Blueprint, jsonify, request
from config import session, CoinBot
from config import Hacks

hacks_bp = Blueprint('hacksRoutes', __name__)

# Gets all the hacks data of a coin
@hacks_bp.route('/api/hacks', methods=['GET'])
def get_hacks():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        coin_bot_name = request.args.get('coin_bot_name')

        if not coin_bot_id and not coin_bot_name:
            return jsonify({'message': 'Coin ID or name is missing', 'status': 400}), 400

        coin_data = None

        if coin_bot_name:
            coin = session.query(CoinBot).filter(CoinBot.name==coin_bot_name).first()
            coin_data = session.query(Hacks).filter_by(coin_bot_id=coin.bot_id).all() if coin else None

        if coin_bot_id:
            coin_data_id = session.query(Hacks).filter_by(coin_bot_id=coin_bot_id).all()
            coin_data = coin_data_id if coin_data_id else None
        
        if coin_data is None:
            # Si no se encuentran hacks para la moneda solicitada, devolver un array vacío en lugar de un mensaje de error.
            return jsonify({'message': [], 'status': 400}), 400

        hacks_list = [hack.as_dict() for hack in coin_data]
        return jsonify({'message': hacks_list, 'status': 200}), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error getting hacks data: {str(e)}', 'status': 500}), 500
    
# Creates a new hack record to a coin
@hacks_bp.route('/api/hacks/create', methods=['POST'])
def create_hack():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')

        if not coin_bot_id:
            return jsonify({'error': 'Coin ID is required', 'status': 400}), 400
        
        # Verificar si el coin_bot_id existe
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_bot_id).first()
        if not coin_bot:
            return jsonify({'error': f'Coin with ID {coin_bot_id} does not exist', 'status': 400}), 400
        
        new_hack = Hacks(
            hack_name=data.get('hackName'),
            date=data.get('date'),
            incident_description=data.get('incidentDescription'),
            consequences=data.get('consequences'),
            mitigation_measure=data.get('mitigationMeasure'),
            coin_bot_id=coin_bot_id
        )
        
        session.add(new_hack)
        session.commit()

        return jsonify({'message': 'New hack record added', 'status': 201}), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'Error creating hack: {str(e)}', 'status': 500}), 500
    
# Edits a hack of a coin 
@hacks_bp.route('/api/hacks/edit/<int:hack_id>', methods=['PUT'])
def edit_hack(hack_id):
    try:
        data = request.json
        hack_to_edit = session.query(Hacks).filter(Hacks.id == hack_id).first()

        if not hack_to_edit:
            return jsonify({'message': 'Hack not found', 'status': 404}), 404

        hack_to_edit.hack_name = data.get('hackName', hack_to_edit.hack_name)
        hack_to_edit.date = data.get('date', hack_to_edit.date)
        hack_to_edit.incident_description = data.get('incidentDescription', hack_to_edit.incident_description)
        hack_to_edit.consequences = data.get('consequences', hack_to_edit.consequences)
        hack_to_edit.mitigation_measure = data.get('mitigationMeasure', hack_to_edit.mitigation_measure)

        session.commit()
        return jsonify({'message': f'Hack updated successfully', 'status': 200}), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error editing hack: {str(e)}', 'status': 500}), 500
    
    
# Deletes a hack record
@hacks_bp.route('/api/hacks/delete/<int:hack_id>', methods=['DELETE'])
def delete_hack(hack_id):
    try:
        hack_to_delete = session.query(Hacks).filter_by(id=hack_id).first()

        if not hack_to_delete:
            return jsonify({'message': 'Hack not found', 'status': 404}), 404

        session.delete(hack_to_delete)
        session.commit()

        return jsonify({'message': 'Hack deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting hack: {str(e)}', 'status': 500}), 500
