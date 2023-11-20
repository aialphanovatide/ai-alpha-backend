from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from models.news_bot.news_bot_model import SCRAPPING_DATA, KEWORDS, BLACKLIST
from routes.news_bot.scrapper import start_periodic_scraping
from apscheduler.jobstores.base import JobLookupError
from config import session, news_bot_start_time
from flask import request, Blueprint
from scheduler import scheduler
from sqlalchemy import exists


scrapper_bp = Blueprint(
    'scrapper_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

def activate_news_bot(target):

    if scheduler.state == 0 or scheduler.state == 2:
        print('Scheduler not active')
        return 'Scheduler not active', 500 
   
    news_bot_job = scheduler.get_job(target)
    if news_bot_job:
        send_notification_to_product_alerts_slack_channel(title_message=f'{target.capitalize()} News Bot is already active',sub_title='Target', message=f'An interval of *{news_bot_start_time} Minutes* has been set for scrapping data')
        return f'{target.capitalize()} News Bot is already active', 400
    else:
        scrapping_data_objects = session.query(SCRAPPING_DATA).filter(SCRAPPING_DATA.main_keyword == target.casefold()).all()

        if not scrapping_data_objects:
            print(f'{target.capitalize()} does not match any in the database')
            return f'{target.capitalize()} does not match any in the database', 404
        
        if scrapping_data_objects:
            main_keyword = scrapping_data_objects[0].main_keyword
            job = scheduler.add_job(start_periodic_scraping, 'interval', minutes=news_bot_start_time, id=target, replace_existing=True, args=[main_keyword], max_instances=1)
            if job:
                send_notification_to_product_alerts_slack_channel(title_message=f'{target.capitalize()} News Bot activated successfully',sub_title='Start', message=f'An interval of *{news_bot_start_time} Minutes* has been set for scrapping data')
                return f'{target.capitalize()} News Bot activated', 200
            else:
                print(f'Error while activating the {target.capitalize()} News Bot')
                return f'Error while activating the {target.capitalize()} News Bot'

    
def deactivate_news_bot(target):

    if scheduler.state == 0 or scheduler.state == 2:
        print('Scheduler not active')
        return 'Scheduler not active', 500 

    try:
        news_bot_job = scheduler.get_job(target)

        if not news_bot_job:
            send_notification_to_product_alerts_slack_channel(title_message=f'{target.capitalize()} News Bot is already inactive',sub_title='Start', message='Inactive')
            return f'{target.capitalize()} News Bot is already inactive', 400
                
        scheduler.remove_job(news_bot_job.id)
        send_notification_to_product_alerts_slack_channel(title_message=f'{target.capitalize()} News Bot deactivated successfully',sub_title='Start', message='Inactive')
        return f'{target.capitalize()} News Bot deactivated', 200
    
    except JobLookupError:
        print(f"{target.capitalize()} News Bot was not found")
        return f"{target.capitalize()} News Bot was not found", 500


# Chnage the time interval of scrapping data    
@scrapper_bp.route('/api/bot/change/interval', methods=['POST'])
def change_time_interval():
    try:
        # Assuming the request contains JSON data with keys 'target' and 'new_interval'
        data = request.get_json()
        target = data.get('target')
        new_interval = data.get('new_interval')

        # Query the database for the record based on the target
        scrapping_data_object = session.query(SCRAPPING_DATA).filter(SCRAPPING_DATA.main_keyword == target.casefold()).first()

        if scrapping_data_object:
            scrapping_data_object.time_interval = new_interval
            session.commit()

            return "Time interval updated successfully", 200
        else:
            return"Record not found", 404

    except Exception as e:
        return "error" + str(e), 500


# Gets the status of the scheduler
@scrapper_bp.route('/api/scheduler/status', methods=['GET'])
def bot_status():
    value = scheduler.state
    if value == 1:
        state = 'Scheduler is active'
    else:
        state = 'Scheduler is not active'

    return state, 200 


# Adds a new keyword to the respective list - BTC, ETH, LSD or Hacks
@scrapper_bp.route('/api/bot/add/keyword', methods=['POST'])
def add_keyword():
    data = request.json
    new_keyword = data['keyword']
    main_keyword = data['main_keyword']

    if not new_keyword or not main_keyword:
        return 'Keyword or main keyword are not present in the request', 404

    if main_keyword and new_keyword:
        scrapping_data_objects = session.query(
            SCRAPPING_DATA).filter(
                SCRAPPING_DATA.main_keyword == main_keyword).all()
        
        if not scrapping_data_objects:
            return 'Main keyword was not found in the database', 404
        
        if scrapping_data_objects:
            keyword_info_id = scrapping_data_objects[0].id
        
            keyword_exists = session.query(exists().where(
                (KEWORDS.keyword == new_keyword.casefold()) &
                (KEWORDS.keyword_info_id == keyword_info_id)
            )).scalar()
            if keyword_exists:
                return f"The keyword '{new_keyword}' already exists in the database for keyword_info_id {keyword_info_id}.", 404
            else:
                new_keyword_object = KEWORDS(keyword=new_keyword.casefold(), keyword_info_id=keyword_info_id)
                session.add(new_keyword_object)
                session.commit()
                return f"The keyword '{new_keyword}' has been inserted into the database for keyword_info_id {keyword_info_id}.", 200


# Adds a new keyword to the respective list - BTC, ETH, LSD or Hacks
@scrapper_bp.route('/api/bot/add/blackword', methods=['POST'])
def add_black_key():
    data = request.json
    new_keyword = data['blackword']
    main_keyword = data['main_keyword']

    if not new_keyword or not main_keyword:
        return 'Keyword or main keyword are not present in the request', 404

    if main_keyword and new_keyword:
        scrapping_data_objects = session.query(
            SCRAPPING_DATA).filter(
                SCRAPPING_DATA.main_keyword == main_keyword).all()
        
        if not scrapping_data_objects:
            return 'Main keyword was not found in the database', 404
        
        if scrapping_data_objects:
            keyword_info_id = scrapping_data_objects[0].id
        
            keyword_exists = session.query(exists().where(
                (BLACKLIST.black_Word == new_keyword.casefold()) &
                (BLACKLIST.keyword_info_id == keyword_info_id)
            )).scalar()
            if keyword_exists:
                return f"The keyword '{new_keyword}' already exists for keyword_info_id {keyword_info_id}.", 404
            else:
                new_keyword_object = BLACKLIST(black_Word=new_keyword.casefold(), keyword_info_id=keyword_info_id)
                session.add(new_keyword_object)
                session.commit()
                return f"The keyword '{new_keyword}' has been inserted into the database for keyword_info_id {keyword_info_id}.", 200
        


# Activates or desactivates a bot by the param target
@scrapper_bp.route('/api/news/bot', methods=['POST'])
def news_bot_commands():
        try:
            data = request.json
            command = data['command']
            target = data['target']

            if command == 'activate': 
                # res, status = activate_news_bot(target)
                res, status = start_periodic_scraping(target)
                return res, status
            elif command == 'deactivate':
                response, status = deactivate_news_bot(target)
                return response, status
            else:
                return 'Command not valid', 400
        except Exception as e:
            print(f'An error occurred: {str(e)}')
            return f'An error occurred: {str(e)}'