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


@competitor_bp.route('/api/competitors/edit', methods=['GET'])
def edit_competitor_data():

    try:
        coin_bot_id = request.args.get('coin_bot_id')
        data = request.data

        if not data:
            return 'Competitor data is required', 400

        if coin_bot_id is None or not coin_bot_id.isdigit():
            return 'Coin is required and must be a non-empty string containing only digits', 400

        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id==coin_bot_id).first()

        if not coin_data:
            return 'No data found for the requested coin', 404
        
        token = coin_data.token

        
        return f'{token} edited successfully', 200
    except Exception as e:
       return f'Error editing competitor data: {str(e)}', 500
    

@competitor_bp.route('/api/competitors', methods=['GET'])
def get_competitor_data():

    try:
        coin_bot_id = request.args.get('coin_bot_id')

        if coin_bot_id is None or not coin_bot_id.isdigit():
            return 'Coin is required and must be a non-empty string containing only digits', 400

        coin_data = session.query(Competitor).filter(Competitor.coin_bot_id == coin_bot_id).first()

        if not coin_data:
            return 'No data found for the requested coin', 404
        
        # competitor_data = 
        print('coin_data: ', coin_data)
        return f'{coin_data.token}', 200
    except Exception as e:
        return f'Error getting competitor data: {str(e)}', 500
