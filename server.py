import os
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
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import Unauthorized
from routes.analysis.google_docs import analysis_bp
from routes.dashboard.activate_all_bots import bots_activator
from routes.dashboard.deactivate_all_bots import bots_deactivator
from routes.dashboard.bots import bots_route
from routes.dashboard.bot_status import bots_status
from routes.dashboard.all_coin_bots import coin_bots
from routes.dashboard.all_keywords import all_keywords
from routes.dashboard.new_chart_s_r import save_new_chart
from routes.dashboard.get_total_bots import total_bots
from routes.dashboard.create_new_keyword import new_keyword
from routes.dashboard.erase_keyword import delete_kw
from routes.chart.last_chart_update import last_chart
from routes.dashboard_access.register import sign_up 
from routes.dashboard_access.sign_in_session import sign_in
from routes.analysis.get_a import get_analysis_by_id
from routes.chart.get_s_r_chart import get_chart_values
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.static_folder = 'static'
app.secret_key = os.urandom(24)

# Register blueprints -  routes
app.register_blueprint(telegram_bp)
app.register_blueprint(scrapper_bp)
app.register_blueprint(send_email_bp)
app.register_blueprint(slack_events_bp)
app.register_blueprint(trendspider_notification_bp)
app.register_blueprint(tradingview_notification_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(bots_activator)
app.register_blueprint(bots_deactivator)
app.register_blueprint(bots_route)
app.register_blueprint(bots_status)
app.register_blueprint(coin_bots)
app.register_blueprint(all_keywords)
app.register_blueprint(save_new_chart)
app.register_blueprint(new_keyword)
app.register_blueprint(delete_kw)
app.register_blueprint(last_chart)
app.register_blueprint(sign_up)
app.register_blueprint(sign_in)
app.register_blueprint(get_analysis_by_id)
app.register_blueprint(total_bots)
app.register_blueprint(get_chart_values)

if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') 
        socketio.run(app, port=9000, debug=False, use_reloader=False) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")
    finally:
        print('---AI Alpha server was stopped---')




