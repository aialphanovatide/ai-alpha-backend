from config import db_url
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
    send_notification_to_product_alerts_slack_channel(title_message=f'{event.job_id} News Bot has an internal error on the last scrapped', sub_title="Response:", message=f"{event.retval}")
    print(f'{event.job_id} has an internal error')

def job_max_instances_reached(event): # for the status with an error of the bot
    job_id = event.job_id
    send_notification_to_product_alerts_slack_channel(title_message=f'{event.job_id} News Bot has an internal error', sub_title="Response:", message=f"Maximum number of running instances reached, consider upgrading the time interval")
    print(f'{job_id} news bot warning. Maximum number of running instances reached, consider upgrading the time interval ')
   
scheduler.add_listener(job_error, EVENT_JOB_ERROR)
scheduler.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)