from config import db_url, session
from config import CoinBot, Category
from routes.news_bot.scrapper import start_periodic_scraping
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES, EVENT_JOB_EXECUTED
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel


scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url= db_url)
if scheduler.state != 1:
    print('-----Scheduler started-----')
    scheduler.start()

def job_executed(event): 
    print(f'\n{event.job_id} was executed successfully at {event.scheduled_run_time}, response: {event.retval}')
    

def job_error(event):
    job_id = str(event.job_id).capitalize()
    message = f'{job_id} has an internal error: {event.retval}'
                                                # layer 0           layer 0
    category = session.query(Category).filter(Category.category == job_id.casefold()).first()

    category.is_active = False
    session.commit()

    send_notification_to_product_alerts_slack_channel(title_message=f'{job_id} News Bot has an internal error on the last scrapped', 
                                                      sub_title="Response", 
                                                      message=f"{event.retval}")
    print(message)

def job_max_instances_reached(event): 
    job_id = str(event.job_id).capitalize() # layer 0 
    message = f'Maximum number of running instances reached, *Upgrade* the time interval'
    
    send_notification_to_product_alerts_slack_channel(title_message=f'{job_id} News Bot - Execution error', 
                                                      sub_title="Response", 
                                                      message=message)
    print(message)
    try:
        target = event.job_id
        scheduler.remove_job(job_id=target)

        with session:

            coin_bots = session.query(CoinBot).filter(CoinBot.bot_name == target.casefold()).first()
            if coin_bots:

                time_interval = coin_bots.time_interval
                bot_name = coin_bots.bot_name

                new_time_interval = int(time_interval) + 5
                coin_bots.time_interval = new_time_interval
                session.commit()


                job = scheduler.add_job(start_periodic_scraping, 'interval', minutes=(new_time_interval), id=target, replace_existing=True, args=[bot_name], max_instances=1)
                if job:
                    send_notification_to_product_alerts_slack_channel(title_message=f'{job_id} News Bot restarted', 
                                                                    sub_title="Response", 
                                                                    message=f"An interval of *{new_time_interval} Minutes* has been set")
                    
                    print(f"""---{job_id} News Bot restarted: An interval of *{new_time_interval} Minutes* has been set for scrapping data---""")
                    
    except Exception as e:
        print(f'---Error while restarting {job_id} News Bot: {str(e)}---')
        send_notification_to_product_alerts_slack_channel(title_message=f'Error while restarting {job_id} News Bot', 
                                                          sub_title="Response", 
                                                          message=f"{str(e)}")
   

   
scheduler.add_listener(job_error, EVENT_JOB_ERROR)
scheduler.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)