import os
from pytz import timezone as tz
from sqlalchemy.engine.url import make_url
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Create a file-based SQLite database URL
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'narrative_trading_scheduler.db')
sqlite_url = make_url(f'sqlite:///{db_path}')

try:
    # Configure job stores
    job_stores = {
        'default': SQLAlchemyJobStore(url=sqlite_url)
    }

    # Configure executors
    executors = {
        'default': ThreadPoolExecutor(20)
    }

    # Set job defaults
    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }

    # Set timezone
    chosen_timezone = tz('America/Argentina/Buenos_Aires')

    # Create and configure the scheduler
    sched = BackgroundScheduler(
        jobstores=job_stores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=chosen_timezone
    )

    # Start the scheduler if it's not already running
    if not sched.running:
        sched.start()
        print('---- Scheduler started for Narrative Trading ----')

except Exception as e:
    print(f"Error starting narrative trading scheduler: {e}")