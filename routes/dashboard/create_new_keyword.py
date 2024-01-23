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


new_keyword = Blueprint('new_kw', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)


@new_keyword.route('/save_keyword', methods=['POST'])
def save_keyword():
    try:
        # Obtener datos del cuerpo de la solicitud (POST request)
        data = request.json

        # Crear una nueva instancia de la clase Keyword con los datos proporcionados
        new_keyword = Keyword(
            word=data.get('keyword'),  # Cambiado de 'keyword' a 'word'
            coin_bot_id=data.get('coin_bot_id')
            # Puedes agregar más campos según sea necesario
        )

        # Guardar el nuevo objeto Keyword en la base de datos
        with DBSession() as db_session:
            db_session.add(new_keyword)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Keyword saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})