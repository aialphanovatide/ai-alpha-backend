import os
import json
from sqlalchemy import func
from dotenv import load_dotenv
from urllib.parse import unquote
from json import JSONDecodeError
from flask import request, Blueprint
# from slackeventsapi import SlackEventAdapter
from config import session, Article, TopStory, TopStoryImage, ArticleImage
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel

load_dotenv()

SLACK_SIGNING_SECRET=os.getenv("SLACK_SIGNING_SECRET")

# slack_events_adapter = SlackEventAdapter(signing_secret=SLACK_SIGNING_SECRET, 
#                                          endpoint="/slack/events", 
#                                          )

slack_events_bp = Blueprint(
    'slack_events_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@slack_events_bp.route('/delete_top_story', methods=['DELETE'])
def delete_top_story():
    id = request.args.get('id')
    if not id:
        return 'Article ID is required', 400

    top_story = session.query(TopStory).filter(TopStory.top_story_id == id).first()

    if not top_story:
        return "Top Story doesn't exist", 404
    else:
        try:
            # Delete related TopStoryImages
            for image in top_story.images:
                session.delete(image)

            # Delete the TopStory
            session.delete(top_story)
            session.commit()
            
            return f"Top Story with ID {id} deleted successfully", 200
        except Exception as e:
            session.rollback()
            return f"Error deleting Top Story: {str(e)}", 500


# RESERVED ROUTE - DO NOT USE
# This route receives all relevant articles that needs to go to the Top Stories
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
            print('Article not found')
            send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX",
                                               title_message="Error saving article in top story section",
                                               sub_title="Response",
                                               message=f"Article with link: {url} - not found")
            return 'Article not found', 404
        
        if article:
            is_top_story_article = session.query(TopStory).filter(TopStory.top_story_id == article.article_id).first()

            if is_top_story_article:
                send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX",
                                               title_message="Error saving article in top story section",
                                               sub_title="Response",
                                               message=f"Article with link: {url} already exist.")
                return 'Article already exist', 409 

            if not is_top_story_article:
                article_image = session.query(ArticleImage).filter(ArticleImage.article_id == article.article_id).first()
                new_topstory = TopStory(coin_bot_id=article.coin_bot_id,
                                        summary=article.summary,
                                        story_date=article.date)
                                
                session.add(new_topstory)
                session.commit()
                
                image = article_image.image if article_image else "No image"
                new_topstory_image = TopStoryImage(image=image,
                                                    top_story_id=new_topstory.top_story_id)
                session.add(new_topstory_image)
                session.commit()

                return 'Message received', 200

    except JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX",
                                               title_message="Error saving article in top story section",
                                               sub_title="Response",
                                               message=f"Error decoding JSON: {e}")
        return 'Bad Request: Invalid JSON', 400

    except KeyError as e:
        print(f"Error accessing key in JSON: {e}")
        send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX",
                                               title_message="Error saving article in top story section",
                                               sub_title="Response",
                                               message=f"Error accessing key in JSON: {e}")
        return 'Bad Request: Missing key in JSON', 400

    except Exception as e:
        print(f"Unexpected error: {e}")
        send_INFO_message_to_slack_channel(channel_id="C06FTS38JRX",
                                               title_message="Error saving article in top story section",
                                               sub_title="Response",
                                               message=f"Unexpected error: {e}")
        return 'Internal Server Error', 500


    

