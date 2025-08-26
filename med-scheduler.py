import schedule
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
import logging
from dotenv import load_dotenv
from notifier import send_sms  # Import from notifier.py; swap for send_email if using email

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
MEDS_FILE = os.getenv("MEDS_FILE", "meds.json")  # Default to meds.json

def load_meds():
    """Load medications from meds.json."""
    try:
        with open(MEDS_FILE, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading meds.json: {e}")
        return []

def send_reminder(med):
    """Send a reminder for a medication."""
    try:
        message = f"Time to take {med['med_amt']} {med['med_name']} at {med['med_time']} on {med['med_date']}."
        send_sms(med.get('phone', os.getenv('DEFAULT_PHONE')), message)  # Use phone from meds.json or env
        logger.info(f"Reminder sent for {med['med_name']} to {med.get('phone', 'default')}")
    except Exception as e:
        logger.error(f"Failed to send reminder for {med['med_name']}: {e}")

def schedule_reminders():
    """Schedule reminders based on meds.json."""
    scheduler = BackgroundScheduler()
    scheduler.start()
    meds = load_meds()

    for med in meds:
        try:
            time_str = med['med_time']
            med_date = med['med_date']
            # Parse time (HH:MM) and date
            job_time = datetime.strptime(time_str, "%H:%M").time()
            job_date = datetime.strptime(med_date, "%Y-%m-%d").date()
            # Schedule for specific date and time
            scheduler.add_job(
                send_reminder,
                'date',
                run_date=datetime.combine(job_date, job_time),
                args=[med]
            )
            logger.info(f"Scheduled reminder for {med['med_name']} at {time_str} on {med_date}")
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid data for {med.get('med_name', 'unknown')}: {e}")

def run_scheduler():
    """Run the scheduler and keep it alive."""
    try:
        schedule_reminders()
        # Keep the script running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")

if __name__ == "__main__":
    run_scheduler()