import json
import os
from flask import Flask
from flask_cors import CORS
from routes.chart.chart import chart_bp
from routes.chart.chart_olhc import chart_graphs_bp
from routes.news_bot.index import scrapper_bp
from routes.telegram.index import telegram_bp
from routes.analysis.analysis import analysis_bp 
from routes.tradingview.index import tradingview_bp
from routes.slack.slack_actions import slack_events_bp
from routes.fundamentals.introduction import introduction
from routes.fundamentals.competitors import competitor_bp
from routes.dashboard_access.access import dashboard_access_bp
from routes.fundamentals.hacks import hacks_bp
from routes.fundamentals.tokenomics import tokenomics
from routes.fundamentals.upgrades import upgrades_bp
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.fundamentals.revenue_model import revenue_model_bp
from routes.fundamentals.dapps import dapps_bp
from routes.news_bot.used_keywords import news_bots_features_bp
from routes.news_bot.index import scrapper_bp
from routes.narrative_trading.narrative_trading import narrative_trading_bp
from routes.user.user import user_bp
from flasgger import Swagger
from ws.socket import init_socketio

app = Flask(__name__)
app.name = 'AI Alpha'
swagger_template_path = os.path.join(app.root_path, 'static', 'swagger_template.json')

# Initialize SocketIO
socketio = init_socketio(app)

with open(swagger_template_path, 'r') as f:
    swagger_template = json.load(f)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, template=swagger_template, config=swagger_config)

CORS(app, origins='*', supports_credentials=True)


app.static_folder = 'static'
app.secret_key = os.urandom(24)


# Register blueprints -  routes
app.register_blueprint(scrapper_bp)
app.register_blueprint(news_bots_features_bp)
app.register_blueprint(chart_bp)
app.register_blueprint(chart_graphs_bp)
app.register_blueprint(dashboard_access_bp)
app.register_blueprint(telegram_bp)
app.register_blueprint(send_email_bp)
app.register_blueprint(competitor_bp)
app.register_blueprint(tradingview_bp)
app.register_blueprint(slack_events_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(hacks_bp)
app.register_blueprint(revenue_model_bp)
app.register_blueprint(introduction)
app.register_blueprint(upgrades_bp)
app.register_blueprint(dapps_bp)
app.register_blueprint(tokenomics)
app.register_blueprint(narrative_trading_bp)
app.register_blueprint(user_bp)


if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') 
        app.run(port=9000, debug=False, use_reloader=False, threaded=True, host='0.0.0.0') 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")
    finally:
        # send_INFO_message_to_slack_channel( channel_id="C06FTS38JRX",
        #                                     title_message="*CRITICAL ERROR*", 
        #                                     sub_title="AI Alpha server has stopped running",
        #                                     message="@David P. - Check this error on the Mac mini immediately")
        print('---AI Alpha server was stopped---')



