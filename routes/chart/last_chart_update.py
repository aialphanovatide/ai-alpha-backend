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


last_chart = Blueprint('lastChartUpdate', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)


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



