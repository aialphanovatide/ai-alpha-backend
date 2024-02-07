import os
from config import Chart, CoinBot
#from routes.slack.templates.product_alert_notification import send_notification_to_product_alerts_slack_channel
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 
from flask import Blueprint

get_chart_values = Blueprint('get_chart_values', __name__)

@get_chart_values.route('/api/coin-support-resistance/<coin_bot_name>', methods=['GET'])
def get_chart_values_by_coin_bot_id(coin_bot_name):
    print(coin_bot_name)
    try:
        with DBSession() as db_session:
            # Buscar el Chart asociado al coin_bot_id
            coinbot = db_session.query(CoinBot).filter(CoinBot.bot_name==coin_bot_name).first()
            chart = db_session.query(Chart).filter_by(coin_bot_id=coinbot.bot_id).first()

            if chart:
                # Construir y devolver un diccionario con los valores de resistencia y soporte
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
                return jsonify({'success': False, 'message': 'Chart not found for the given coin_bot_id'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})