from collections import defaultdict
import re
from config import CoinBot, Competitor, session, Session
from flask import Blueprint, request, jsonify

from services.coingecko.coingecko import get_competitors_data, get_tokenomics_data


competitor_bp = Blueprint('competitor_bp', __name__)

def normalize_key(key):
    return re.sub(r'[^a-zA-Z0-9]', '', key.lower())

# edits a competitor data by the ID of the competitor
@competitor_bp.route('/edit_competitors/<int:competitor_id>', methods=['PUT'])  
def edit_competitor_data(competitor_id):
    try:
        data = request.json
        coin_data = session.query(Competitor).filter(Competitor.id == competitor_id).first()
        
        if not coin_data:
            return {'message': 'No data found for the requested coin'}, 404

        for key, value in data['competitor_data'].items():
            if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                setattr(coin_data, key, value)

        session.commit()
        return {'message': f'{coin_data.token} edited successfully'}, 200
    
    except Exception as e:
        return {'error': f'Error editing competitor data: {str(e)}'}, 500
    
@competitor_bp.route('/get_competitors/<int:coin_bot_id>', methods=['GET'])
def get_competitor_data(coin_bot_id):
    try:
        if coin_bot_id is None:
            return jsonify({'message': 'Coin ID is required', 'status': 400}), 400

        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id == coin_bot_id).all()

        if not coin_data:
            return jsonify({'message': 'No data found for the requested coin', 'status': 404}), 404

        token_data = defaultdict(lambda: {'symbol': '', 'attributes': {}})

        for competitor in coin_data:
            token = competitor.token.strip().upper()
            key = competitor.key.strip()
            value = competitor.value

            if not token_data[token]['symbol']:
                token_data[token]['symbol'] = token
            
            token_data[token]['attributes'][key] = {
                'value': value,
                'is_coingecko_data': False,
                'id': competitor.id
            }

        for token in token_data:
            coingecko_data = get_competitors_data(token)
            if isinstance(coingecko_data, dict):
                for tokenomics_key, tokenomics_value in coingecko_data.items():
                    normalized_tokenomics_key = normalize_key(tokenomics_key)
                    matched = False
                    for existing_key in list(token_data[token]['attributes'].keys()):
                        if set(normalized_tokenomics_key.split()) & set(normalize_key(existing_key).split()):
                            token_data[token]['attributes'][existing_key] = {
                                'value': tokenomics_value,
                                'is_coingecko_data': True,
                                'id': token_data[token]['attributes'][existing_key]['id']
                            }
                            matched = True
                            break
                    if not matched:
                        token_data[token]['attributes'][tokenomics_key] = {
                            'value': tokenomics_value,
                            'is_coingecko_data': True,
                            'id': None
                        }

        # Crear el objeto final
        final_data = {}
        for token, data in token_data.items():
            final_data[token] = {
                'symbol': data['symbol'],
                'attributes': {k: v for k, v in data['attributes'].items() if v['value'] is not None}
            }

        return jsonify({'competitors': final_data, 'status': 200}), 200
    
    except Exception as e:
        original_data = {}
        for competitor in coin_data:
            token = competitor.token.strip().upper()
            if token not in original_data:
                original_data[token] = {'symbol': token, 'attributes': {}}
            original_data[token]['attributes'][competitor.key.strip()] = {
                'value': competitor.value,
                'is_coingecko_data': False,
                'id': competitor.id
            }

        return jsonify({
            'competitors': original_data, 
            'status': 200, 
            'message': f'Error processing data, returning original data: {str(e)}'
        }), 200

#APP GET COMPETITORS ROUTE
# Gets a list of the competitors and the analyzed coin  
@competitor_bp.route('/api/get_competitors_by_coin_name', methods=['GET'])
def get_competitor_data_by_coin_name():
    try:
        coin_name = request.args.get('coin_name')
        if not coin_name:
            return jsonify({'message': 'Coin name is required', 'status': 400}), 400

        coinbot = session.query(CoinBot).filter(CoinBot.name == coin_name).first()
        if not coinbot:
            return jsonify({'message': 'CoinBot not found for the given coin name', 'status': 404}), 404

        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id == coinbot.bot_id).all()

        if not coin_data:
            return jsonify({'message': 'No data found for the requested coin', 'status': 404}), 404

        competitor_data = [{
            'competitor': competitor_value.as_dict(),
        } for competitor_value in coin_data]
        
        return jsonify({'competitors': competitor_data, 'status': 200}), 200
    
    except Exception as e:
        return jsonify({'message': f'Error getting competitors data: {str(e)}', 'status': 500}), 500



# Builder to create competitor table
@competitor_bp.route('/create_competitor', methods=['POST'])
def create_competitor_table():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')

        if coin_bot_id is None:
            return jsonify({'error': 'Coin ID is required', 'status': 400}), 400

        competitor_data = data.get('competitor_data')

        if not competitor_data:
            return jsonify({'error': 'Competitor data is required', 'status': 400}), 400
        
        token=competitor_data.get('token')
        data=competitor_data.get('data')

        if not token or not data:
            return jsonify({'error': 'Token or data is missing', 'status': 400}), 400
        
        for obj in data:
            key = obj['key'].lower()  
            value = obj['value'].lower()  
            new_competitor = Competitor(
                token=token.lower(),  
                key=key,
                value=value,
                coin_bot_id=coin_bot_id
            )

            session.add(new_competitor)
            session.commit()

        return jsonify({'message': 'Features added successfully', 'status': 201}), 201
    
    except Exception as e:
        return jsonify({'error': f'Error creating competitor: {str(e)}', 'status': 500}), 500



# Deletes a competitor record
@competitor_bp.route('/delete_competitor/<int:competitor_id>', methods=['DELETE'])
def delete_competitor(competitor_id):
    try:
        competitor_to_delete = session.query(Competitor).filter_by(id=competitor_id).first()

        if not competitor_to_delete:
            return jsonify({'message': 'Competitor not found', 'status': 404}), 404

        session.delete(competitor_to_delete)
        session.commit()

        return jsonify({'message': 'Competitor deleted successfully', 'status': 200}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'message': f'Error deleting competitor: {str(e)}', 'status': 500}), 500
