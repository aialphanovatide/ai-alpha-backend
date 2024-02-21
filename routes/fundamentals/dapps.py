from flask import Blueprint, jsonify, request
from config import Session, DApps, session, CoinBot

dapps_bp = Blueprint('dappsRoutes', __name__)

# Gets all the dapps data of a coin
@dapps_bp.route('/api/dapps', methods=['GET'])
def get_dapps():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        coin_bot_name = request.args.get('coin_bot_name')

        if not coin_bot_id and not coin_bot_name:
            return jsonify({'message': 'Coin ID or name is missing', 'status': 400}), 400

        coin_data = None
        if coin_bot_name:
            coin = session.query(CoinBot).filter(CoinBot.bot_name==coin_bot_name).first()
            coin_data = session.query(DApps).filter_by(coin_bot_id=coin.bot_id).all() if coin else None

        if coin_bot_id:
            dapps = session.query(DApps).filter_by(coin_bot_id=coin_bot_id).all()
            coin_data = dapps if dapps else None

        if coin_data is None:
            return jsonify({'message': 'No hacks found for the requested coin', 'status': 404}), 404

        dapps_list = [dapp.as_dict() for dapp in coin_data]
        return jsonify({'message': dapps_list, 'status': 200}), 200
    
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'Error getting DApps data: {str(e)}', 'status': 500}), 500

# Creates a new dapps record for a coin
@dapps_bp.route('/api/dapps/create', methods=['POST'])
def create_dapp():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')

        if not coin_bot_id:
            return jsonify({'message': 'Coin ID is missing', 'status': 400}), 400

        new_dapp = DApps(
            dapps=data.get('dapps'),
            description=data.get('description'),
            tvl=data.get('tvl'),
            coin_bot_id=coin_bot_id
        )

        session.add(new_dapp)
        session.commit()
        return jsonify({'message': f'DApp record created successfully', 'status': 201}), 201
    
    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error creating DApp: {str(e)}', 'status': 500}), 500

# Edits a dapss record of a coin
@dapps_bp.route('/api/dapps/edit/<int:dapp_id>', methods=['PUT'])
def edit_dapp(dapp_id):
    try:
        data = request.json
        dapp = session.query(DApps).filter_by(id=dapp_id).first()

        if not dapp:
            return jsonify({'message': 'DApp not found', 'status': 404}), 404

        dapp.dapps = data.get('dapps', dapp.dapps)
        dapp.description = data.get('description', dapp.description)
        dapp.tvl = data.get('tvl', dapp.tvl)

        session.commit()
        return jsonify({'message': 'DApp updated successfully', 'status': 200}), 200  

    except Exception as e:
        return jsonify({'message': f'Error updating DApp: {str(e)}', 'status': 500}), 500


# Deletes a dapps record of a coin
@dapps_bp.route('/api/dapps/delete/<int:dapp_id>', methods=['DELETE'])
def delete_dapp(dapp_id):
    try:
        dapp = session.query(DApps).filter_by(id=dapp_id).first()

        if not dapp:
            return jsonify({'message': 'DApp not found', 'status': 404}), 404

        session.delete(dapp)
        session.commit()
        return jsonify({'message': 'DApp deleted successfully', 'status': 200}), 200  

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting DApp: {str(e)}', 'status': 500}), 500
