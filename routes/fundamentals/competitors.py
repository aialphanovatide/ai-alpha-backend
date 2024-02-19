from config import Competitor, session
from flask import Blueprint, request, jsonify


competitor_bp = Blueprint('competitor_bp', __name__)


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
    

# Gets a list of the competitors and the analyzed coin  
@competitor_bp.route('/get_competitors/<int:coin_bot_id>', methods=['GET'])
def get_competitor_data(coin_bot_id):
    try:
        if coin_bot_id is None:
            return jsonify({'message': 'Coin ID is required', 'status': 400}), 400

        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id == coin_bot_id).all()

        if not coin_data:
            return jsonify({'message': 'No data found for the requested coin', 'status': 404}), 404

        competitor_data = [{
            'competitor': competitor_value.as_dict(),
        } for competitor_value in coin_data]
        
        return jsonify({'competitors': competitor_data, 'status': 200}), 200
    
    except Exception as e:
        return jsonify({'message': f'Error getting competitors data: {str(e)}', 'status': 500}), 500


# Creates a new competitor for a coin
# @competitor_bp.route('/post_competitor', methods=['POST'])
# def create_competitor():
#     try:
#         data = request.json
#         coin_bot_id = data.get('coin_bot_id')

#         if coin_bot_id is None:
#             return jsonify({'error': 'Coin ID is required', 'status': 400}), 400

#         competitor_data = data.get('competitor_data')

#         if not competitor_data:
#             return jsonify({'error': 'Competitor data is required', 'status': 400}), 400

#         # Crea una nueva instancia de Competitor con los datos recibidos
#         new_competitor = Competitor(
#             token=competitor_data.get('token', None),
#             circulating_supply=competitor_data.get('circulating_supply', None),
#             token_supply_model=competitor_data.get('token_supply_model', None),
#             current_market_cap=competitor_data.get('current_market_cap', None),
#             tvl=competitor_data.get('tvl', None),
#             daily_active_users=competitor_data.get('daily_active_users', None),
#             transaction_fees=competitor_data.get('transaction_fees', None),
#             transaction_speed=competitor_data.get('transaction_speed', None),
#             inflation_rate_2022=competitor_data.get('inflation_rate_2022', None),
#             inflation_rate_2023=competitor_data.get('inflation_rate_2023', None),
#             apr=competitor_data.get('apr', None),
#             active_developers=competitor_data.get('active_developers', None),
#             revenue=competitor_data.get('revenue', None),
#             total_supply=competitor_data.get('total_supply', None),
#             percentage_circulating_supply=competitor_data.get('percentage_circulating_supply', None),
#             max_supply=competitor_data.get('max_supply', None),
#             coin_bot_id=coin_bot_id
#         )

#         session.add(new_competitor)
#         session.commit()
#         return jsonify({'message': f'Competitor for coin_bot_id {coin_bot_id} created successfully', 'status': 201}), 201
    
#     except Exception as e:
#         return jsonify({'error': f'Error creating competitor: {str(e)}', 'status': 500}), 500
    

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

        return jsonify({'message': f'Competitor for coin_bot_id {coin_bot_id} created successfully', 'status': 201}), 201
    
    except Exception as e:
        return jsonify({'error': f'Error creating competitor: {str(e)}', 'status': 500}), 500



# Route to edit an already created competitor