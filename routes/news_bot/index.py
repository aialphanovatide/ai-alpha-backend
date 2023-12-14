from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from config import CoinBot, Blacklist, session, Alert, Category, Article
from routes.news_bot.scrapper import start_periodic_scraping
from apscheduler.jobstores.base import JobLookupError
from flask import request, Blueprint
from scheduler import scheduler
from sqlalchemy import exists
import traceback

scrapper_bp = Blueprint(
    'scrapper_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


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
            
        job = scheduler.add_job(start_periodic_scraping, 'interval', minutes=time_interval, id=category_name, replace_existing=True, args=[category_name], max_instances=1)
        if job:
            print(f'{category_name.capitalize()} activated successfully')
        
        message = f'{category_name.capitalize()} activated successfully'
        # send_notification_to_product_alerts_slack_channel(title_message=message, sub_title='Message', message=f'An interval of *{time_interval} Minutes* has been set for scrapping data')
        return f'{category_name.capitalize()} News Bot activated', 200

    except Exception as e:
        print(f'Error while activating the {category_name.capitalize()} News Bot: {str(e)}')
        return f'Error while activating the {category_name.capitalize()} News Bot', 500


    
def deactivate_news_bot(category_name):
    try:
        if not scheduler.state:
            print('Scheduler not active')
            return 'Scheduler not active', 500

        category = session.query(Category).filter(Category.category == category_name).first()

        if not category:
            print(f'{category_name.capitalize()} does not match any in the database')
            return f'{category_name.capitalize()} does not match any in the database', 404

       
        scheduler.remove_job(category_name)

        message = f'{category_name.capitalize()} deactivated successfully'
        # send_notification_to_product_alerts_slack_channel(title_message=message, sub_title='Status', message='Inactive')
        return f'{category_name.capitalize()} deactivated', 200

    except Exception as e:
        print(f'Error while deactivating {category_name.capitalize()}: {str(e)}')
        return f'Error while deactivating {category_name.capitalize()}: {str(e)}', 500


def get_news(bot_name):
    try:
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).first()

        if not coin_bot:
            return {'error': f'Bot "{bot_name}" not found'}, 404

        coin_bot_id = coin_bot.bot_id

        articles = session.query(Article).filter(Article.coin_bot_id == coin_bot_id).all()

        if articles:
            articles_list = []

            for article in articles:
                article_dict = {
                    'article_id': article.article_id,
                    'date': article.date,
                    'title': article.title,
                    'url': article.url,
                    'summary': article.summary,
                    'created_at': article.created_at.isoformat(),  # Convert to ISO format
                    'coin_bot_id': article.coin_bot_id,
                    'images': []
                }

                # Include image information
                for image in article.images:
                    article_dict['images'].append({
                        'image_id': image.image_id,
                        'image': image.image,
                        'created_at': image.created_at.isoformat(),  # Convert to ISO format
                        'article_id': image.article_id
                    })

                articles_list.append(article_dict)

            return {'articles': articles_list}, 200
        else:
            return {'message': f'No articles found for {bot_name}'}, 404
 
    except Exception as e:
        traceback.print_exc()
        return {'error': f'An error occurred getting the news for {bot_name}: {str(e)}'}, 500

@scrapper_bp.route('/api/get/news', methods=['GET'])  
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
    
def get_alerts(bot_name):
    try:
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).first()

        if not coin_bot:
            return {'error': f'Bot "{bot_name}" not found'}, 404

        coin_bot_id = coin_bot.bot_id

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
            return {'message': f'No alerts found for {bot_name}'}, 404
   
    except Exception as e:
        traceback.print_exc()  # Log the full stack trace
        return {'error': f'An error occurred getting the alerts for {bot_name}: {str(e)}'}, 500
    

@scrapper_bp.route('/api/get/alerts', methods=['GET'])
def get_alerts_route():
    try:
        data = request.json
        bot_name = data.get('botName')

        if not bot_name:
            return {'error': 'Bot name is required in the request'}, 400

        result, status_code = get_alerts(bot_name=bot_name)

        return result, status_code
    except Exception as e:
        return {'error': f'An error occurred: {str(e)}'}, 500


# Activates or desactivates a bot by the param target
@scrapper_bp.route('/api/news/bot', methods=['POST'])
def news_bot_commands():
        try:
            data = request.json
            command = data['command']
            category = data['category']
            category = str(category).casefold()

            if command == 'activate': 
                res, status = activate_news_bot(category)
                # res, status = start_periodic_scraping(category)
                return res, status
            elif command == 'deactivate':
                response, status = deactivate_news_bot(category)
                return response, status
            else:
                return 'Command not valid', 400
        except Exception as e:
            print(f'An error occurred: {str(e)}')
            return f'An error occurred: {str(e)}'
        



# # Chnage the time interval of scrapping data    
# @scrapper_bp.route('/api/bot/change/interval', methods=['POST'])
# def change_time_interval():
#     try:
#         # Assuming the request contains JSON data with keys 'target' and 'new_interval'
#         data = request.get_json()
#         target = data.get('target')
#         new_interval = data.get('new_interval')

#         # Query the database for the record based on the target
#         scrapping_data_object = session.query(CoinBot).filter(CoinBot.bot_name == target.casefold()).first()

#         if scrapping_data_object:
#             scrapping_data_object.time_interval = new_interval
#             session.commit()

#             return f"Time interval updated successfully to {new_interval}", 200
#         else:
#             return"Record not found", 404

#     except Exception as e:
#         return "error" + str(e), 500


# # Gets the status of the scheduler
# @scrapper_bp.route('/api/scheduler/status', methods=['GET'])
# def bot_status():
#     value = scheduler.state
#     if value == 1:
#         state = 'Scheduler is active'
#     else:
#         state = 'Scheduler is not active'

#     return state, 200 


# # Adds a new keyword to the respective list - BTC, ETH, LSD or Hacks
# @scrapper_bp.route('/api/bot/add/keyword', methods=['POST'])
# def add_keyword():
#     data = request.json
#     new_keyword = data['keyword']
#     main_keyword = data['main_keyword']

#     if not new_keyword or not main_keyword:
#         return 'Keyword or main keyword are not present in the request', 404

#     if main_keyword and new_keyword:
#         scrapping_data_objects = session.query(
#             CoinBot).filter(
#                 CoinBot.bot_name == main_keyword).all()
        
#         if not scrapping_data_objects:
#             return 'Main keyword was not found in the database', 404
        
#         if scrapping_data_objects:
#             keyword_info_id = scrapping_data_objects[0].bot_id
        
#             keyword_exists = session.query(exists().where(
#                 (Keyword.word == new_keyword.casefold()) &
#                 (Keyword.coin_bot_id == keyword_info_id)
#             )).scalar()
#             if keyword_exists:
#                 return f"The keyword '{new_keyword}' already exists in the database for keyword_info_id {keyword_info_id}.", 404
#             else:
#                 new_keyword_object = Keyword(word=new_keyword.casefold(), coin_bot_id=keyword_info_id)
#                 session.add(new_keyword_object)
#                 session.commit()
#                 return f"The keyword '{new_keyword}' has been inserted into the database for keyword_info_id {CoinBot}.", 200


# # Adds a new keyword to the respective list - BTC, ETH, LSD or Hacks
# @scrapper_bp.route('/api/bot/add/blackword', methods=['POST'])
# def add_black_key():
#     data = request.json
#     new_keyword = data['blackword']
#     main_keyword = data['main_keyword']

#     if not new_keyword or not main_keyword:
#         return 'Keyword or main keyword are not present in the request', 404

#     if main_keyword and new_keyword:
#         scrapping_data_objects = session.query(
#             CoinBot).filter(
#                 CoinBot.bot_name == main_keyword).all()
        
#         if not scrapping_data_objects:
#             return 'Main keyword was not found in the database', 404
        
#         if scrapping_data_objects:
#             keyword_info_id = scrapping_data_objects[0].id
        
#             keyword_exists = session.query(exists().where(
#                 (Blacklist.word == new_keyword.casefold()) &
#                 (Blacklist.coin_bot_id == keyword_info_id)
#             )).scalar()
#             if keyword_exists:
#                 return f"The keyword '{new_keyword}' already exists for keyword_info_id {keyword_info_id}.", 404
#             else:
#                 new_keyword_object = Blacklist(word=new_keyword.casefold(), coin_bot_id=keyword_info_id)
#                 session.add(new_keyword_object)
#                 session.commit()
#                 return f"The keyword '{new_keyword}' has been inserted into the database for keyword_info_id {keyword_info_id}.", 200
        