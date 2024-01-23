import os
import bcrypt
from config import Admin, Analysis, AnalysisImage, Category, Chart, CoinBot, Keyword
#from routes.slack.templates.product_alert_notification import send_notification_to_product_alerts_slack_channel
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.trendspider.index import trendspider_notification_bp
from routes.tradingview.index import tradingview_notification_bp
from routes.news_bot.index import activate_news_bot, deactivate_news_bot, scrapper_bp
from routes.telegram.index import telegram_bp 
from routes.slack.slack_actions import slack_events_bp
from flask_cors import CORS
from websocket.socket import socketio
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 
from flask import Blueprint

get_chart_values = Blueprint('get_chart_values', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)

@get_chart_values.route('/api/coin-support-resistance/<int:coin_bot_id>', methods=['GET'])
def get_chart_values_by_coin_bot_id(coin_bot_id):
    try:
        with DBSession() as db_session:
            # Buscar el Chart asociado al coin_bot_id
            chart = db_session.query(Chart).filter_by(coin_bot_id=coin_bot_id).first()

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