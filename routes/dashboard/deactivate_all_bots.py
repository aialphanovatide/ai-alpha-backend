from flask import Blueprint, request
import base64
import os
from config import Category
from routes.news_bot.index import activate_news_bot, deactivate_news_bot, scrapper_bp
from routes.telegram.index import telegram_bp 
from routes.slack.slack_actions import slack_events_bp
from flask_cors import CORS
from websocket.socket import socketio
from flask import Flask, jsonify, render_template, session as flask_session
from flask import request, redirect, url_for
from config import Session as DBSession 


app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)

bots_deactivator = Blueprint('bots_deactivator', __name__)


@bots_deactivator.route('/deactivate_all_bots', methods=['POST'])
def deactivate_bot():
    try:
        with DBSession() as db_session:
            categories = db_session.query(Category).all()

        for category in categories:
            deactivate_news_bot(category.category)

        any_inactive = any(not category.is_active for category in categories)
        return jsonify({"bots": [{"category": category.category, "isActive": category.is_active} for category in categories], "any_inactive": any_inactive})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
