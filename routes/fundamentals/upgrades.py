from config import Upgrades, session, CoinBot
from flask import Blueprint, request, jsonify


upgrades_bp = Blueprint('upgrades_bp', __name__)


# Gets the upgrades data related to a coin
@upgrades_bp.route('/api/get_upgrades', methods=['GET'])
def get_upgrades():

    try:
        coin_bot_id = request.args.get('coin_bot_id')
        coin_name = request.args.get('coin_name')

        if not coin_bot_id and not coin_name:
            return jsonify({'message': 'Coin ID or name is missing', 'status': 400}), 400

        coin_data = None

        if coin_name:
            coin = session.query(CoinBot).filter(CoinBot.name==coin_name).first()
            coin_data = session.query(Upgrades).filter_by(coin_bot_id=coin.bot_id).all() if coin else None

        if coin_bot_id:
            coin_data_id = session.query(Upgrades).filter_by(coin_bot_id=coin_bot_id).all()
            coin_data = coin_data_id if coin_data_id else None
        
        if coin_data is None:
            return jsonify({'message': 'No upgrades found for the requested coin', 'status': 404}), 404
       
        upgrades = [{'upgrade': upgrade.as_dict()} for upgrade in coin_data]
        return jsonify({'message': upgrades, 'status': 200}), 200

    except Exception as e:
        return jsonify({'message': f'Error getting the upgrades data, {str(e)}', 'status': 500}), 500


# Post a new upgrade record
@upgrades_bp.route('/post_upgrade', methods=['POST'])
def post_upgrades():

    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')

        if coin_bot_id is None:
            return jsonify({'message': 'Coin ID is required', 'status': 400}), 400

        upgrade_data = data.get('upgrade_data')

        if not upgrade_data:
            return jsonify({'message': 'Upgrade data is required', 'status': 400}), 400

        new_upgrade = Upgrades(
            coin_bot_id=coin_bot_id,
            event=upgrade_data.get('event', None),
            date=upgrade_data.get('date', None),
            event_overview=upgrade_data.get('event_overview', None),
            impact=upgrade_data.get('impact', None)
        )

        session.add(new_upgrade)
        session.commit()

        return jsonify({'message': 'Upgrade data added', 'status': 200}), 200

    except Exception as e:
        return jsonify({'message': f'Error getting the upgrades data, {str(e)}', 'status': 500}), 500


# Edits an upgrade record
@upgrades_bp.route('/edit_upgrade/<int:upgrate_id>', methods=['PUT'])
def edit_upgrade_data(upgrate_id):
    try:
        data = request.json
        coin_data = session.query(Upgrades).filter(
            Upgrades.id == upgrate_id).first()
      
        if not coin_data:
            return jsonify({'message': 'No data found for the requested coin', 'status': 404}), 404

        if not data['upgrate_data'].items():
            return jsonify({'message': f'Upgrade data requried', 'status': 400}), 400

        for key, value in data['upgrate_data'].items():
            if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                setattr(coin_data, key, value)

        session.commit()
        return jsonify({'message': f'Upgrade edited successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error editing competitor data: {str(e)}', 'status': 500}), 500

# Deletes an upgrade record
@upgrades_bp.route('/delete_upgrade/<int:upgrade_id>', methods=['DELETE'])
def delete_upgrade(upgrade_id):
    try:
        upgrade = session.query(Upgrades).filter_by(id=upgrade_id).first()

        if not upgrade:
            return jsonify({'message': 'Upgrade not found', 'status': 404}), 404

        session.delete(upgrade)
        session.commit()

        return jsonify({'message': 'Upgrade deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting upgrade: {str(e)}', 'status': 500}), 500
