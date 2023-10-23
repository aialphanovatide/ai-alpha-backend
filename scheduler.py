from config import db_url, news_bot_start_time, session
from models.news_bot.news_bot_model import SCRAPPING_DATA
from routes.news_bot.scrapper import start_periodic_scraping
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES, EVENT_JOB_EXECUTED
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel


scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url= db_url)
if scheduler.state != 1:
    print('Scheduler started')
    scheduler.start()


def job_executed(event): # for the status 200 of the bot
    print(f'{event.job_id} was executed successfully at {event.scheduled_run_time}, response: {event.retval}')

def job_error(event): # for the status with an error of the bot
    job_id = str(event.job_id).capitalize()
    send_notification_to_product_alerts_slack_channel(title_message=f'{job_id} News Bot has an internal error on the last scrapped', 
                                                      sub_title="Response:", 
                                                      message=f"{event.retval}")
    print(f'{job_id} has an internal error:\ne{event.retval}')

def job_max_instances_reached(event): # for the status with an error of the bot
    job_id = str(event.job_id).capitalize()
    message = f'Maximum number of running instances reached'
    send_notification_to_product_alerts_slack_channel(title_message=f'{job_id} News Bot - Execution error', 
                                                      sub_title="Response:", 
                                                      message=message)
    try:
        target = event.job_id
        scheduler.remove_job(job_id=target)
        
        scrapping_data_objects = session.query(SCRAPPING_DATA).filter(SCRAPPING_DATA.main_keyword == target.casefold()).all()
        main_keyword = scrapping_data_objects[0].main_keyword

        job = scheduler.add_job(start_periodic_scraping, 'interval', minutes=(news_bot_start_time + 5), id=target, replace_existing=True, args=[main_keyword], max_instances=1)
        if job:
            send_notification_to_product_alerts_slack_channel(title_message=f'{job_id} News Bot restarted', 
                                                              sub_title="Response:", 
                                                              message=f"Execution of {job_id} News Bot restarted successfully")
            print(f"""{job_id} News Bot restarted\n
                    An interval of *{news_bot_start_time + 5} Minutes* has been set for scrapping data')""")
    except Exception as e:
        print(f'Error while restarting {job_id} News Bot\n{str(e)}')
        send_notification_to_product_alerts_slack_channel(title_message=f'Error while restarting {job_id} News Bot', 
                                                          sub_title="Response:", 
                                                          message=f"str(e)")
   

   
scheduler.add_listener(job_error, EVENT_JOB_ERROR)
scheduler.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)