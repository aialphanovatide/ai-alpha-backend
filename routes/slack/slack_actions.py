from slackeventsapi import SlackEventAdapter
from flask import request, Blueprint
from json import JSONDecodeError
from urllib.parse import unquote
from dotenv import load_dotenv
import json
from websocket.socket import socketio
from sqlalchemy import func
from config import session, Article, TopStory
import os

load_dotenv()

SLACK_SIGNING_SECRET=os.getenv("SLACK_SIGNING_SECRET")

slack_events_adapter = SlackEventAdapter(signing_secret=SLACK_SIGNING_SECRET, 
                                         endpoint="/slack/events", 
                                         )

slack_events_bp = Blueprint(
    'slack_events_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@slack_events_bp.route("/slack/events", methods=["POST"])
def slack_events():
    try:
        # data = request.json

        # if 'challenge' in data:
        #     challenge = data['challenge']
        #     return challenge, 200

        data = request.get_data().decode('utf-8')  # Decode the bytes to a string
        payload = unquote(data.split('payload=')[1])  # Extract and decode the payload

        payload_dict = json.loads(payload)
        value = payload_dict['actions'][0]['value']
        
        # Decode the URL-encoded value and replace '+' with spaces
        url = unquote(value).replace('+', ' ').strip()
        url = url.split('linkToArticle:')[1]
        
        article = session.query(Article).filter(func.trim(Article.url) == url.strip()).first()
        if not article:
            return 'Article not found', 404
        
        if article:
            new_topstory = TopStory(coin_bot_id=article.coin_bot_id,
                     summary=article.summary,
                     story_date=article.date)
            
            session.add(new_topstory)
            session.commit()

            socketio.emit('update_topstory', namespace='/topstory')
            return 'Message received', 200

    except JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return 'Bad Request: Invalid JSON', 400

    except KeyError as e:
        print(f"Error accessing key in JSON: {e}")
        return 'Bad Request: Missing key in JSON', 400

    except Exception as e:
        print(f"Unexpected error: {e}")
        return 'Internal Server Error', 500


    

