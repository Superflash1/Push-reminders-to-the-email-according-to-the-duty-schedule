from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.services.reminder_service import run_reminder_once

scheduler = BackgroundScheduler()


def _job_runner():
    db = SessionLocal()
    try:
        run_reminder_once(db)
    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(_job_runner, "interval", minutes=1, id="reminder_job", replace_existing=True)
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
