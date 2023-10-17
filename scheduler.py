from config import db_url
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MAX_INSTANCES, EVENT_JOB_EXECUTED

scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url= db_url)
if scheduler.state != 1:
    scheduler.start()


def job_executed(event): # for the status 200 of the bot
    print(f'{event.job_id} was executed successfully at {event.scheduled_run_time}, response: {event.retval}')

def job_error(event): # for the status with an error of the bot
    print(f'{event.job_id} has an internal error')

def job_max_instances_reached(event): # for the status with an error of the bot
    job_id = event.job_id
    print(f'{job_id} news bot warning. Maximum number of running instances reached, consider upgrading the time interval ')
   
scheduler.add_listener(job_error, EVENT_JOB_ERROR)
scheduler.add_listener(job_max_instances_reached, EVENT_JOB_MAX_INSTANCES)
scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)