import os
from config import Admin, Analysis, AnalysisImage, Category, Chart, CoinBot, Keyword
#from routes.slack.templates.product_alert_notification import send_notification_to_product_alerts_slack_channel
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.trendspider.index import trendspider_notification_bp
from routes.tradingview.index import tradingview_bp
from routes.news_bot.index import activate_news_bot, deactivate_news_bot, scrapper_bp
from routes.telegram.index import telegram_bp 
from routes.slack.slack_actions import slack_events_bp
from flask_cors import CORS
from websocket.socket import socketio
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 
from flask import Blueprint


save_new_chart = Blueprint('saveChart', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)


@save_new_chart.route('/save_chart', methods=['POST'])
def save_chart():
    try:
        # Obtener datos del cuerpo de la solicitud (POST request)
        data = request.json

        # Crear una nueva instancia de la clase Chart con los datos proporcionados
        new_chart = Chart(
            support_1=data.get('support_1'),
            support_2=data.get('support_2'),
            support_3=data.get('support_3'),
            support_4=data.get('support_4'),
            resistance_1=data.get('resistance_1'),
            resistance_2=data.get('resistance_2'),
            resistance_3=data.get('resistance_3'),
            resistance_4=data.get('resistance_4'),
            coin_bot_id=data.get('coin_bot_id')
            # Puedes agregar más campos según sea necesario
        )

        # Eliminar todas las filas donde coin_bot_id sea igual al proporcionado
        with DBSession() as db_session:
            delete_last_chart = db_session.query(Chart).filter_by(coin_bot_id=data.get('coin_bot_id')).delete()
            print(f"{delete_last_chart} rows deleted")

            # Guardar el nuevo objeto Chart en la base de datos
            db_session.add(new_chart)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Chart saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})