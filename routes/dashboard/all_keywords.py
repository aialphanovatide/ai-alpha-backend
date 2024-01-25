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


all_keywords = Blueprint('getAllKeywords', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)


@all_keywords.route('/get_keywords_for_coin_bot/<int:coin_bot_id>', methods=['GET'])
def get_keywords_for_coin_bot(coin_bot_id):
    print(coin_bot_id)
    try:
        with DBSession() as db_session:
            # Obtener las palabras clave para el coinBot específico
            keywords = db_session.query(Keyword).filter_by(coin_bot_id=coin_bot_id).all()
            keywords_data = [{'id': keyword.keyword_id, 'word': keyword.word} for keyword in keywords]
            return jsonify({'success': True, 'keywords': keywords_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})