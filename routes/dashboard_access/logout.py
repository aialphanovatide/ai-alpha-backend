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


sign_out = Blueprint('signUp', __name__)

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')
socketio.init_app(app)

# Configure Flask to look for templates in the 'dashboard/templates' folder
app.template_folder = 'dashboard/apps/templates'
app.static_folder = 'dashboard/apps/static'
app.secret_key = os.urandom(24)



@sign_out.route('/logout', methods=['POST'])
def signup():
    if request.method == 'POST':
        # Obtener datos del formulario
        data = request.json  # Utiliza request.json para obtener datos JSON directamente
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        print('pass: ', password)
        print('user: ', username)
        print('email: ', email)

        # Verificar que la contraseña no sea None
        if password is None:
            return jsonify({'success': False, 'message': 'Invalid password'})

        # Crear un nuevo objeto Admin y guardar en la base de datos
        new_admin = Admin(username=username, mail=email, password=password)

        # Utiliza la sesión de SQLAlchemy que has definido en config.py
        with DBSession() as db_session:
            db_session.add(new_admin)
            db_session.commit()

        # Puedes devolver un JSON indicando el éxito del registro
        return jsonify({'success': True, 'message': 'Registration successful'})

    # Si la solicitud no es POST, devolver un mensaje de error
    return jsonify({'success': False, 'message': 'Invalid request'})