# Note: This specific file was completely coded by AI, I've yet to learn about SMTP and focus mainly on higher level production.

import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Email config from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = os.getenv("TO_EMAIL")

def send_email(to, subject, body):
    """
    Send an email reminder using SMTP.
    Requires environment variables for SMTP settings and recipient email.
    """
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")

def send_reminder(med):
    """
    Send a medication reminder email.
    """
    subject = f"Medication Reminder: {med['med_name']}"
    body = f"Time to take {med['med_amt']} {med['med_name']} at {med['med_time']} on {med['med_date']}."
    send_email(TO_EMAIL, subject, body)
