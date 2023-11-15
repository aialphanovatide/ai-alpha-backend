from slackeventsapi import SlackEventAdapter
from flask import request, Blueprint
from json import JSONDecodeError
from urllib.parse import unquote
from dotenv import load_dotenv
import json
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
        data = request.get_data().decode('utf-8')  # Decode the bytes to a string
        payload = unquote(data.split('payload=')[1])  # Extract and decode the payload

        payload_dict = json.loads(payload)
        value = payload_dict['actions'][0]['value']
        
        # Decode the URL-encoded value and replace '+' with spaces
        decoded_value = unquote(value).replace('+', ' ')

        # If you want to split the decoded value into two parts (Testing summary and 11/14/2023)
        text, date = decoded_value.split(',')

        print('text > ', text)
        print('date > ', date)

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