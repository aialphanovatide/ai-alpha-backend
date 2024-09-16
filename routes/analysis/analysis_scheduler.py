# Scheduler for the Analysis, and handling of errors

import os
from pytz import timezone as tz
from sqlalchemy.engine.url import make_url
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from services.slack.slack_services import send_INFO_message_to_slack_channel
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES, EVENT_JOB_MISSED

SLACK_LOGS_CHANNEL_ID = 'C06FTS38JRX'

# Create a file-based SQLite database URL
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'analysis_scheduler.db')
sqlite_url = make_url(f'sqlite:///{db_path}')

try:
    # Configure the job stores and executors
    job_stores = {
    'default': SQLAlchemyJobStore(url=sqlite_url)
    }
    executors = {
        'default': ThreadPoolExecutor(20)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }

    chosen_timezone = tz('America/Argentina/Buenos_Aires')

    # Create the scheduler with the SQLite job store
    sched = BackgroundScheduler(
        jobstores=job_stores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=chosen_timezone
    )

    if sched.state != 1:
        sched.start()
        print('---- Scheduler started for the Analysis ----')

except Exception as e:
    print(f"Error starting analysis scheduler: {e}")



def job_error(event):
    send_INFO_message_to_slack_channel(channel_id=SLACK_LOGS_CHANNEL_ID,
                                       title_message=f'Analysis Post Failed', 
                                       sub_title="Response", 
                                       message=f"Job ID: {event.job_id}\nResponse: {event.retval}")


def job_max_instances_reached(event):  
    send_INFO_message_to_slack_channel(channel_id=SLACK_LOGS_CHANNEL_ID,
                                    title_message='Analysis Post Failed', 
                                    sub_title="Response", 
                                    message=f'Job ID: {event.job_id}\nMaximum number of running instances reached, *Upgrade* the time interval'
                                    )          

def job_missed(event):
    send_INFO_message_to_slack_channel(channel_id=SLACK_LOGS_CHANNEL_ID,
                                    title_message='Analysis Post Failed', 
                                    sub_title="Response", 
                                    message=f'Job ID: {event.job_id}\nMissed execution, check the job details and configuration'
                                    )
  
   

   
sched.add_listener(job_error, EVENT_JOB_ERROR)
sched.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
sched.add_listener(job_missed, EVENT_JOB_MISSED)