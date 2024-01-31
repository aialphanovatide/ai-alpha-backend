from config import Competitor, session
from flask import Blueprint, request


competitor_bp = Blueprint('competitor_bp', __name__)


# # Create a Competitor instance with sample data
# competitor_data = Competitor(
#     token='SampleToken',
#     circulating_supply='100000000',
#     token_supply_model='Fixed Supply',
#     current_market_cap='1000000000',
#     tvl='500000000',
#     daily_active_users='10000',
#     transaction_fees='0.01',
#     transaction_speed='Fast',
#     Inflation_rate='5%',
#     apr='10%',
#     active_developers=20,
#     revenue=500000,
#     coin_bot_id=1
# )

# session.add(competitor_data)
# session.commit()

@competitor_bp.route('/api/competitors/edit', methods=['GET', 'POST'])  
def edit_competitor_data():
    try:
        data = request.json

        if 'coin_bot_id' not in data or not data['coin_bot_id'].isdigit():
            return {'error': 'Coin is required and must be a non-empty string containing only digits'}, 400

        coin_bot_id = data['coin_bot_id']
        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id == coin_bot_id).first()

        if not coin_data:
            return {'error': 'No data found for the requested coin'}, 404

        # Actualiza los campos del objeto coin_data con los datos recibidos
        for key, value in data['competitor_data'].items():
            if key not in ['coin_bot_id', 'updated_at', 'created_at', 'dynamic']:
                setattr(coin_data, key, value)

        session.commit()

        token = coin_data.token
        return {'message': f'{token} edited successfully'}, 200
    except Exception as e:
        return {'error': f'Error editing competitor data: {str(e)}'}, 500
    
    
@competitor_bp.route('/api/competitors', methods=['GET'])
def get_competitor_data():
    try:
        coin_bot_id = request.args.get('coin_bot_id')
        print(coin_bot_id)
        if coin_bot_id is None or not coin_bot_id.isdigit():
            return 'Coin is required and must be a non-empty string containing only digits', 400

        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id == coin_bot_id).all()

        if not coin_data:
            return 'No data found for the requested coin', 404

        # Utiliza el método as_dict para convertir cada Competitor a un diccionario
        competitors_list = [competitor.as_dict() for competitor in coin_data]
        print('coin_data: ', competitors_list)
        return {'competitors': competitors_list}, 200
    except Exception as e:
        return f'Error getting competitor data: {str(e)}', 500
    
@competitor_bp.route('/api/competitors/create', methods=['POST'])
def create_competitor():
    try:
        data = request.json  # Obtén todo el cuerpo JSON
        coin_bot_id = data.get('coin_bot_id')  # Obtén coin_bot_id del cuerpo JSON

        print('coinbot recibido', coin_bot_id)
        print('data recibida', data)
        
        # Crear un nuevo competidor asociado al coin_bot_id
        new_competitor = Competitor(
            token=data.get('competitor_data').get('token'),
            circulating_supply=data.get('competitor_data').get('circulating_supply'),
            token_supply_model=data.get('competitor_data').get('token_supply_model'),
            current_market_cap=data.get('competitor_data').get('current_market_cap'),
            tvl=data.get('competitor_data').get('tvl'),
            daily_active_users=data.get('competitor_data').get('daily_active_users'),
            transaction_fees=data.get('competitor_data').get('transaction_fees'),
            transaction_speed=data.get('competitor_data').get('transaction_speed'),
            inflation_rate=data.get('competitor_data').get('inflation_rate'),
            apr=data.get('competitor_data').get('apr'),
            active_developers=data.get('competitor_data').get('active_developers'),
            revenue=data.get('competitor_data').get('revenue'),
            coin_bot_id=coin_bot_id
        )

        session.add(new_competitor)
        session.commit()

        return {'message': f'Competitor for coin_bot_id {coin_bot_id} created successfully'}, 201
    except Exception as e:
        return {'error': f'Error creating competitor: {str(e)}'}, 500

