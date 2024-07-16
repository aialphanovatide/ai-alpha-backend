import requests
from sqlalchemy import and_
from config import Chart, Session, session, CoinBot
from flask import jsonify, request, Blueprint, jsonify  
from datetime import datetime

chart_bp = Blueprint('chart', __name__)


# ----- ROUTE FOR THE DASHBOARD -------------------------------------------
# Deletes the last support and resistance lines of a coin and adds new ones.
@chart_bp.route('/save_chart', methods=['POST'])
def save_chart():
    try:
        data = request.json
        coin_bot_id = data.get('coin_bot_id')
        pair = data.get('pair')
        temporality = data.get('temporality')
        token = data.get('token')


        if not coin_bot_id or not pair or not temporality or not token:
            return jsonify({'success': False, 'message': 'One or more fields are missing'}), 400

        if token.casefold() == 'btc' and pair.casefold() == 'btc':
            return jsonify({'success': False, 'message': 'Coin/pair not valid'}), 400
        
        existing_chart = session.query(Chart).filter(Chart.coin_bot_id==coin_bot_id, 
                                                     Chart.pair==pair.casefold(), 
                                                     Chart.temporality==temporality.casefold(),
                                                     Chart.token==token.casefold()).first()


        if existing_chart:
            # Update existing chart values
            existing_chart.support_1 = data.get('support_1')
            existing_chart.support_2 = data.get('support_2')
            existing_chart.support_3 = data.get('support_3')
            existing_chart.support_4 = data.get('support_4')
            existing_chart.resistance_1 = data.get('resistance_1')
            existing_chart.resistance_2 = data.get('resistance_2')
            existing_chart.resistance_3 = data.get('resistance_3')
            existing_chart.resistance_4 = data.get('resistance_4')

            session.commit()

            return jsonify({'success': True, 'message': 'Chart updated successfully'}), 200
        else:
            # Create a new chart
            new_chart = Chart(
                support_1=data.get('support_1'),
                support_2=data.get('support_2'),
                support_3=data.get('support_3'),
                support_4=data.get('support_4'),
                resistance_1=data.get('resistance_1'),
                resistance_2=data.get('resistance_2'),
                resistance_3=data.get('resistance_3'),
                resistance_4=data.get('resistance_4'),
                token=token,
                pair=pair,
                temporality=data.get('temporality'),
                coin_bot_id=coin_bot_id
            )

            session.add(new_chart)
            session.commit()

            return jsonify({'success': True, 'message': 'Chart created successfully'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

    


# ----- ROUTE FOR THE APP ---------------------------
# Gets the support and resistance lines of a requested coin
@chart_bp.route('/api/coin-support-resistance', methods=['GET'])
def get_chart_values_by_coin_bot_id():

    try:
        coin_name = request.args.get('coin_name')
        temporality = request.args.get('temporality')
        pair = request.args.get('pair')
        
        if not all([coin_name, temporality, pair]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})

        coinbot = session.query(CoinBot).filter(CoinBot.bot_name == coin_name).first()
        if not coinbot:
            return jsonify({'success': False, 'message': 'CoinBot not found for the given coin name'})
        
        chart = session.query(Chart).filter_by(coin_bot_id=coinbot.bot_id, temporality=temporality, pair=pair).first()
        if chart:
            chart_values = {
                'support_1': chart.support_1,
                'support_2': chart.support_2,
                'support_3': chart.support_3,
                'support_4': chart.support_4,
                'resistance_1': chart.resistance_1,
                'resistance_2': chart.resistance_2,
                'resistance_3': chart.resistance_3,
                'resistance_4': chart.resistance_4,
                'token': chart.token,
                'pair': chart.pair,
                'temporality': chart.temporality
            }
            return jsonify({'success': True, 'chart_values': chart_values})
        else:
            return jsonify({'success': False, 'message': 'Chart not found for the given parameters'})

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})



# ----- ROUTE FOR THE DASHBOARD ---------------------------
# Gets the support and resistance lines of a requested coin
# this route is duplicated with the previous one, just for convenience, as the dashboard is passing the ID of the coin.
@chart_bp.route('/api/coin-support-resistance/dashboard', methods=['GET'])
def get_s_and_r():

    try:
        coin_id=request.args.get('coin_id')
        temporality=request.args.get('temporality')
        pair=request.args.get('pair')

        if coin_id is None or temporality is None or pair is None:
            return jsonify({'success': False, 'message': 'One or more values are missing'}), 400

        chart = session.query(Chart).filter(Chart.coin_bot_id==coin_id,Chart.pair==pair.casefold(),Chart.temporality==temporality.casefold()).first()

        if chart:
            chart_values = {
                'support_1': chart.support_1,
                'support_2': chart.support_2,
                'support_3': chart.support_3,
                'support_4': chart.support_4,
                'resistance_1': chart.resistance_1,
                'resistance_2': chart.resistance_2,
                'resistance_3': chart.resistance_3,
                'resistance_4': chart.resistance_4,
                'token': chart.token,
                'pair': chart.pair,
                'temporality': chart.temporality
            }

            return jsonify({'success': True, 'chart_values': chart_values}), 200
        else:
            return jsonify({'success': False, 'message': 'Chart not found for the given coin ID'}), 204

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    



# ---------------- Route for TOTAL3 DATA --------------------------------

@chart_bp.route('/api/total_3_data', methods=['GET'])
def get_total_3_data():
    try:
        url_btc = "https://pro-api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7&interval=daily"
        url_eth = "https://pro-api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=7&interval=daily"
        url_total = "https://pro-api.coingecko.com/api/v3/global/market_cap_chart?days=7"

        headers = {"x-cg-pro-api-key": "CG-xXCJJaHa7QmvQNWyNheKmSfG"}

        btc_response = requests.get(url_btc, headers=headers)
        eth_response = requests.get(url_eth, headers=headers)
        total_response = requests.get(url_total, headers=headers)

        btc_response.raise_for_status()
        eth_response.raise_for_status()
        total_response.raise_for_status()

        data_eth = eth_response.json()
        data_total = total_response.json()
        data_btc = btc_response.json()

        btc_market_caps = [entry[1] for entry in data_btc["market_caps"]]
        eth_market_caps = [entry[1] for entry in data_eth["market_caps"]]
        total_market_caps = [entry[1] for entry in data_total["market_cap_chart"]["market_cap"]]

        eth_btc_market_caps = [btc_market_caps[i] + eth_market_caps[i] for i in range(len(btc_market_caps))]
        total_market_cap = total_market_caps

        total3 = [total_market_cap[i] - eth_btc_market_caps[i] for i in range(len(total_market_cap))]

        return jsonify({"data": total3})

    except requests.exceptions.RequestException as e:
        print("Error", str(e))
        return jsonify({"error": "Error " + str(e)})




# Gets the last chart updated with Support and resistance lines - Return a DATE
@chart_bp.route('/get_last_chart_update', methods=['GET'])
def get_last_chart_update():
    try:
        with Session() as db_session:
            last_update = (
                db_session.query(Chart, CoinBot.bot_name)
                .outerjoin(CoinBot, Chart.coin_bot_id == CoinBot.bot_id)
                .order_by(Chart.created_at.desc())
                .first()
            )

        if last_update:
            chart, bot_name = last_update
            formatted_date = chart.created_at.strftime('%m/%d/%Y %H:%M')

            return jsonify({
                'success': True,
                'last_update': {
                    'coin_bot_name': bot_name,
                    'formatted_date': formatted_date
                }
            })
        else:
            return jsonify({'success': False, 'message': 'there is no updates available'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


