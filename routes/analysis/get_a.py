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


get_analysis_by_id = Blueprint('getAnalysisID', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)



@get_analysis_by_id.route('/get_analysis/<int:coin_bot_id>', methods=['GET'])
def get_analysis(coin_bot_id):
    with DBSession() as db_session:
        analysis_objects = db_session.query(Analysis).filter_by(coin_bot_id=coin_bot_id).all()

       
        analysis_data = []
        for analy in analysis_objects:
            analysis_dict = analy.to_dict() 

            images_objects = db_session.query(AnalysisImage).filter_by(analysis_id=analy.analysis_id).all()
            images_data = [{'image_id': img.image_id, 'image': img.image} for img in images_objects]

            analysis_dict['analysis_images'] = images_data
            analysis_data.append(analysis_dict)

        for analy in analysis_data:
            print(f"Analysis ID: {analy['analysis_id']}, Analysis: {analy['analysis']}, Created At: {analy['created_at']}")
            for img in analy['analysis_images']:
                print(f"  Image ID: {img['image_id']}, Image: {img['image']}")

        return jsonify(analysis_data)
