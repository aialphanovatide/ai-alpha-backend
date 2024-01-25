import os

import bcrypt
from config import Admin, Analysis, AnalysisImage, Category, Chart, CoinBot, Keyword, Session
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
from routes.dashboard.activate_all_bots import bots_activator
from routes.dashboard.deactivate_all_bots import bots_deactivator
from routes.dashboard.bots import bots_route
from routes.news_bot.index import scrapper_bp
from routes.telegram.index import telegram_bp 
from routes.tradingview.index import tradingview_bp
from routes.dashboard.bot_status import bots_status
from routes.dashboard.all_coin_bots import coin_bots
from routes.dashboard.erase_keyword import delete_kw
from routes.dashboard_access.register import sign_up 
from routes.analysis.get_a import get_analysis_by_id
from routes.chart.last_chart_update import last_chart
from routes.slack.slack_actions import slack_events_bp
from routes.dashboard.all_keywords import all_keywords
from routes.dashboard.get_total_bots import total_bots
from routes.chart.get_s_r_chart import get_chart_values
from routes.dashboard.new_chart_s_r import save_new_chart
from routes.dashboard_access.sign_in_session import sign_in
from routes.dashboard.create_new_keyword import new_keyword
from routes.dashboard.activate_all_bots import bots_activator
from routes.trendspider.index import trendspider_notification_bp
from routes.dashboard.deactivate_all_bots import bots_deactivator
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel

app = Flask(__name__)
app.name = 'AI Alpha'

CORS(app, origins='*')

# Init of Socket
socketio.init_app(app)

app.static_folder = 'static'
app.secret_key = os.urandom(24)

# Register blueprints -  routes
app.register_blueprint(sign_up)
app.register_blueprint(sign_in)
app.register_blueprint(coin_bots)
app.register_blueprint(delete_kw)
app.register_blueprint(bots_route)
app.register_blueprint(last_chart)
app.register_blueprint(total_bots)
app.register_blueprint(scrapper_bp)
app.register_blueprint(send_email_bp)
app.register_blueprint(slack_events_bp)
app.register_blueprint(trendspider_notification_bp)
app.register_blueprint(tradingview_notification_bp)
app.register_blueprint(bots_activator)
app.register_blueprint(bots_deactivator)
app.register_blueprint(bots_route)
app.register_blueprint(bots_status)
app.register_blueprint(telegram_bp)
app.register_blueprint(new_keyword)
app.register_blueprint(all_keywords)
app.register_blueprint(send_email_bp)
app.register_blueprint(save_new_chart)
app.register_blueprint(bots_activator)
app.register_blueprint(tradingview_bp)
app.register_blueprint(slack_events_bp)
app.register_blueprint(bots_deactivator)
app.register_blueprint(get_chart_values)
app.register_blueprint(get_analysis_by_id)
app.register_blueprint(trendspider_notification_bp)



#route to post analysis
@app.route('/post_analysis', methods=['POST'])
def post_analysis():
    try:
        coin_bot_id = request.form.get('coinBot')
        content = request.form.get('content')
        image_file = request.files.get('image')

        print(f'Coin Bot ID: {coin_bot_id}')
        print(f'Content: {content}')

        with DBSession() as db_session:
            new_analysis = Analysis(
                analysis=content,
                coin_bot_id=coin_bot_id 
            )
            db_session.add(new_analysis)
            db_session.commit()

            if image_file:
                image_data = image_file.read()
                new_analysis_image = AnalysisImage(
                    image=image_data,
                    analysis_id=new_analysis.analysis_id,
                )
                db_session.add(new_analysis_image)
                db_session.commit()

        return 'Analysis sent successfully', 200

    except Exception as e:
        print(f'Error found: {str(e)}')
        return f'Error found: {str(e)}', 500


if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') 
        socketio.run(app, port=9000, debug=False, use_reloader=False) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")
    finally:
        # send_INFO_message_to_slack_channel( channel_id="C06FTS38JRX",
        #                                     title_message="*CRITICAL ERROR*", 
        #                                     sub_title="AI Alpha server has stop running",
        #                                     message="@David P. - Check this error on the Mac mini immediately")
        print('---AI Alpha server was stopped---')




