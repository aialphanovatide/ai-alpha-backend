from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from routes.telegram.email_invitation_link.invitation_link import send_email_bp
from routes.trendspider.index import trendspider_notification_bp
from routes.tradingview.index import tradingview_notification_bp
from routes.news_bot.index import scrapper_bp
from routes.telegram.index import telegram_bp 
from flask_cors import CORS
from flask import Flask

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')

app.register_blueprint(telegram_bp)
app.register_blueprint(scrapper_bp)
app.register_blueprint(send_email_bp)
app.register_blueprint(trendspider_notification_bp)
app.register_blueprint(tradingview_notification_bp)



if __name__ == '__main__':
    try:
        # send_notification_to_product_alerts_slack_channel(title_message='AI Alpha Server is running', message="Message:", sub_title="All dependencies are working")
        print('---AI Alpha server is running---') # Once the server is ready. Add a pin message to slack
        app.run(threaded=True, debug=False, port=9000, use_reloader=True) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")      

# send_notification_to_product_alerts_slack_channel(title_message='AI Alpha Server is down', message="Message:", sub_title="----")
print('---AI Alpha server was stopped---')