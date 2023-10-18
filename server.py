from routes.trendspider.index import trendspider_notification_bp
from routes.news_bot.index import scrapper_bp
from routes.telegram.index import telegram_bp 
from flask_cors import CORS
from flask import Flask

app = Flask(__name__)
app.name = 'AI Alpha'
CORS(app, origins='*')

app.register_blueprint(telegram_bp)
app.register_blueprint(scrapper_bp)
app.register_blueprint(trendspider_notification_bp)



if __name__ == '__main__':
    try:
        print('---AI Alpha server is running---') # Once the server is ready. Add a pin message to slack
        app.run(threaded=True, debug=False, port=8000, use_reloader=True) 
    except Exception as e:
        print(f"Failed to start the AI Alpha server: {e}")      

print('---AI Alpha server was stopped---')