from config import Chart, session, CoinBot
from flask import jsonify, request, Blueprint, jsonify

chart_bp = Blueprint('chart', __name__)


# ----- ROUTE FOR THE DASHBOARD -------------------------------------------
# Deletes the last support and resistance lines of a coin and adds new ones.
@chart_bp.route('/save_chart', methods=['POST'])
def save_chart():
    try:
        data = request.json
        print('data: ', data)
        coin_bot_id = data.get('coin_bot_id')

        if not coin_bot_id:
            return jsonify({'success': False, 'message': 'Coin ID required'}), 400

        print('coin_bot_id: ', coin_bot_id)
        delete_last_chart = session.query(Chart).filter_by(coin_bot_id=coin_bot_id).delete()
        print(f"{delete_last_chart} rows deleted")

        new_chart = Chart(
            support_1=data.get('support_1'),
            support_2=data.get('support_2'),
            support_3=data.get('support_3'),
            support_4=data.get('support_4'),
            resistance_1=data.get('resistance_1'),
            resistance_2=data.get('resistance_2'),
            resistance_3=data.get('resistance_3'),
            resistance_4=data.get('resistance_4'),
            coin_bot_id=coin_bot_id
        )

        session.add(new_chart)
        session.commit()

        return jsonify({'success': True, 'message': 'Chart updated successfully'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    


# ----- ROUTE FOR THE DASHBOARD ---------------------------
# Gets the support and resistance lines of a requested coin
@chart_bp.route('/api/coin-support-resistance/<coin_bot_name>', methods=['GET'])
def get_chart_values_by_coin_bot_id(coin_bot_name):

    try:
           
        coinbot = session.query(CoinBot).filter(CoinBot.bot_id==coin_bot_name).first()
        chart = session.query(Chart).filter_by(coin_bot_id=coinbot.bot_id).first()

        if chart:
            chart_values = {
                'support_1': chart.support_1,
                'support_2': chart.support_2,
                'support_3': chart.support_3,
                'support_4': chart.support_4,
                'resistance_1': chart.resistance_1,
                'resistance_2': chart.resistance_2,
                'resistance_3': chart.resistance_3,
                'resistance_4': chart.resistance_4
            }

            return jsonify({'success': True, 'chart_values': chart_values})
        else:
            return jsonify({'success': False, 'message': 'Chart not found for the given coin ID'})

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    


