import os
from pytz import timezone as tz
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Create a file-based SQLite database URL
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'narrative_trading_scheduler.db')
sqlite_url = make_url(f'sqlite:///{db_path}')

print(f"Attempting to create database at: {db_path}")

try:
    # Explicitly create the database
    engine = create_engine(sqlite_url)
    engine.connect()

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

    if not sched.running:
        sched.start()
        print('---- Scheduler started for Narrative Trading ----')
    else:
        print('---- Scheduler already running ----')

    # Verify if the database file was created
    if os.path.exists(db_path):
        print(f"Database file created successfully at {db_path}")
    else:
        print(f"Failed to create database file at {db_path}")

except Exception as e:
    print(f"Error initializing scheduler: {e}")