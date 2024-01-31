from config import Chart, CoinBot
from flask import jsonify
from config import Session as DBSession 
from flask import Blueprint


last_chart = Blueprint('lastChartUpdate', __name__)

@last_chart.route('/get_last_chart_update', methods=['GET'])
def get_last_chart_update():
    try:
        with DBSession() as db_session:
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



