from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from config import CoinBot, session, Alert, Category, Article, TopStory
from routes.news_bot.scrapper import start_periodic_scraping
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime, timedelta
from flask import request, Blueprint
from scheduler import scheduler
from sqlalchemy import exists
from sqlalchemy import desc
import traceback

scrapper_bp = Blueprint(
    'scrapper_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


# Gets all top stories 
def get_all_top_stories():
    try:
        coin_bots = session.query(CoinBot).all()

        if not coin_bots:
            return {'message': 'No CoinBots found'}, 404

        top_stories_list = []

        for coin_bot in coin_bots:
            coin_bot_id = coin_bot.bot_id

            # Sort the top stories by creation date in descending order
            top_stories = session.query(TopStory).filter(TopStory.coin_bot_id == coin_bot_id).order_by(desc(TopStory.created_at)).all()

            for top_story in top_stories:
                top_story_dict = {
                    'top_story_id': top_story.top_story_id,
                    'story_date': top_story.story_date,
                    'summary': top_story.summary,
                    'created_at': top_story.created_at.isoformat(),
                    'coin_bot_id': top_story.coin_bot_id,
                    'images': []
                }

                for image in top_story.images:
                    top_story_dict['images'].append({
                        'image_id': image.image_id,
                        'image': image.image,
                        'created_at': image.created_at.isoformat(),
                        'top_story_id': image.top_story_id
                    })

                top_stories_list.append(top_story_dict)

        if top_stories_list:
            return {'top_stories': top_stories_list}, 200
        else:
            return {'message': 'No top stories found'}, 404

    except Exception as e:
        return {'error': f'An error occurred getting the top stories: {str(e)}'}, 500

@scrapper_bp.route('/api/get/allTopStories', methods=['GET'])
def get_all_top_stories_route():
    try:
        result, status_code = get_all_top_stories()
        return result, status_code

    except Exception as e:
        return {'error': f'An error occurred getting the news: {str(e)}'}, 500
    


# Gets all the news related to a category: ex Layer 0 
def get_news(bot_name):
    try:
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).first()

        if not coin_bot:
            return {'error': f'Bot "{bot_name}" not found'}, 404

        coin_bot_id = coin_bot.bot_id

        # Sort the articles by date in descending order
        articles = session.query(Article).filter(Article.coin_bot_id == coin_bot_id).order_by(desc(Article.date)).all()

        if articles:
            articles_list = []

            for article in articles:
                article_dict = {
                    'article_id': article.article_id,
                    'date': article.date,
                    'title': article.title,
                    'url': article.url,
                    'summary': article.summary,
                    'created_at': article.created_at.isoformat(),
                    'coin_bot_id': article.coin_bot_id,
                    'images': []
                }

                # Include image information
                for image in article.images:
                    article_dict['images'].append({
                        'image_id': image.image_id,
                        'image': image.image,
                        'created_at': image.created_at.isoformat(),
                        'article_id': image.article_id
                    })

                articles_list.append(article_dict)

            return {'articles': articles_list}, 200
        else:
            return {'message': f'No articles found for {bot_name}'}, 404
 
    except Exception as e:
        traceback.print_exc()
        return {'error': f'An error occurred getting the news for {bot_name}: {str(e)}'}, 500

@scrapper_bp.route('/api/get/news', methods=['GET', 'POST'])  
def get_news_by_bot_name():
    try:
        data = request.json
        bot_name = data.get('botName')

        if not bot_name:
            return {'error': 'Bot name is required in the request'}, 400

        res, status = get_news(bot_name=bot_name)

        return res, status
    except Exception as e:
        traceback.print_exc() 
        return {'error': f'An error occurred getting the news: {str(e)}'}, 500


def get_alerts(bot_name, date_option='today'):
    try:
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).first()

        if not coin_bot:
            return {'error': f'Bot "{bot_name}" not found'}, 404

        coin_bot_id = coin_bot.bot_id

        # Determine the date range based on the provided option
        if date_option == 'today':
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            print('start_date: ', start_date)
        elif date_option == 'this week':
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            print('start_date: ', start_date)
        elif date_option == 'last week':
            today = datetime.now()
            start_date = today - timedelta(days=(today.weekday() + 7))
            print('start_date: ', start_date)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = None

        # Filter alerts based on date range
        if start_date:
            alerts = session.query(Alert).filter(Alert.coin_bot_id == coin_bot_id, Alert.created_at >= start_date).all()
        else:
            alerts = session.query(Alert).filter(Alert.coin_bot_id == coin_bot_id).all()

        if alerts:
            # Convert alerts to a list of dictionaries
            alerts_list = []

            for alert in alerts:
                alert_dict = {
                    'alert_id': alert.alert_id,
                    'alert_name': alert.alert_name,
                    'alert_message': alert.alert_message,
                    'symbol': alert.symbol,
                    'price': alert.price,
                    'coin_bot_id': alert.coin_bot_id,
                    'created_at': alert.created_at.isoformat()  # Convert to ISO format
                }

                alerts_list.append(alert_dict)

            return {'alerts': alerts_list}, 200
        else:
            return {'message': f'No alerts found for {bot_name} on {date_option}'}, 404

    except Exception as e:
        traceback.print_exc()  # Log the full stack trace
        return {'error': f'An error occurred getting the alerts for {bot_name}: {str(e)}'}, 500


@scrapper_bp.route('/api/get/alerts', methods=['GET', 'POST'])
def get_alerts_route():
    try:
        data = request.json
        bot_name = data.get('botName')
        date_option = data.get('dateOption', None)

        if not bot_name:
            return {'error': 'Bot name is required in the request'}, 400

        result, status_code = get_alerts(bot_name=bot_name, date_option=date_option)

        return result, status_code
    except Exception as e:
        return {'error': f'An error occurred: {str(e)}'}, 500



@scrapper_bp.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        categories = session.query(Category).filter(Category.category != 'hacks').order_by(Category.category_id).all()
        category_data = []

        for category in categories:
            category_data.append({
                'category_id': category.category_id,
                'category': category.category,
                'time_interval': category.time_interval,
                'is_active': category.is_active,
                'image': category.image,
                'created_at': category.created_at.isoformat(),
                'coin_bots': [{
                    'bot_id': bot.bot_id,
                    'bot_name': bot.bot_name,
                    'image': bot.image,
                    'created_at': bot.created_at.isoformat()
                } for bot in category.coin_bot]
            })

        return {'categories': category_data}, 200

    except Exception as e:
        return {'error': str(e)}, 500



def activate_news_bot(category_name):
    try:
        if not scheduler.state:
            print('Scheduler not active')
            return 'Scheduler not active', 500
        
        category = session.query(Category).filter(Category.category == category_name.casefold()).first()
        
        if not category:
            print(f'{category_name.capitalize()} does not match any in the database')
            return f'{category_name.capitalize()} does not match any in the database', 404
        
        time_interval = category.time_interval
        category.is_active = True
        session.commit()
            
        job = scheduler.add_job(start_periodic_scraping, 'interval', minutes=time_interval, id=category_name, replace_existing=True, args=[category_name], max_instances=2)
        if job:
            print(f'{category_name.capitalize()} activated successfully')
        
        message = f'{category_name.capitalize()} activated successfully'
        send_notification_to_product_alerts_slack_channel(title_message=message, sub_title='Message', message=f'An interval of *{time_interval} Minutes* has been set for scrapping data')
        return f'{category_name.capitalize()} News Bot activated', 200

    except Exception as e:
        print(f'Error while activating the {category_name.capitalize()} News Bot: {str(e)}')
        return f'Error while activating the {category_name.capitalize()} News Bot', 500


    
def deactivate_news_bot(category_name):

    try:
        category = session.query(Category).filter(Category.category == category_name).first()

        if not category:
            print(f'{category_name.capitalize()} does not match any in the database')
            return f'{category_name.capitalize()} does not match any in the database', 404


        scheduler.remove_job(category_name)
        category.is_active = False
        session.commit()

        message = f'{category_name.capitalize()} deactivated successfully'
        send_notification_to_product_alerts_slack_channel(title_message=message, sub_title='Status', message='Inactive')
        return f'{category_name.capitalize()} deactivated', 200
    
    except JobLookupError as e:
        print(f'{category_name.capitalize()} News Bot not found: {str(e)}')
        return f'{category_name.capitalize()} News Bot not found: {str(e)}', 500

    except Exception as e:
        print(f'Error while deactivating {category_name.capitalize()}: {str(e)}')
        return f'Error while deactivating {category_name.capitalize()}: {str(e)}', 500


# Activates or desactivates a category: ex Layer 0  
@scrapper_bp.route('/api/news/bot', methods=['POST'])
def news_bot_commands():
        
        try:
            data = request.json
            command = data['command']
            category = data['category']
            category = str(category).casefold()

            if command == 'activate': 
                res, status = activate_news_bot(category)
                return res, status
            elif command == 'deactivate':
                response, status = deactivate_news_bot(category)
                return response, status
            else:
                return 'Command not valid', 400
        except Exception as e:
            print(f'An error occurred: {str(e)}')
            return f'An error occurred: {str(e)}'
        


    #  initial_time = time.time()
    #             res, status = activate_news_bot(category)
    #             # res, status = start_periodic_scraping(category)
    #             final_time = time.time()
    #             final_scrapping_time = final_time - initial_time
    #             minutes, seconds = divmod(final_scrapping_time, 60)
    #             print(f"Final time: {minutes:.0f} minutes and {seconds:.2f} seconds")
    #             return res, status