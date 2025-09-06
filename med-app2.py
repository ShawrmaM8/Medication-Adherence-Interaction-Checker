import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from fuzzywuzzy import fuzz
import streamlit as st
from dotenv import load_dotenv
import os
import smtplib

from email.mime.text import MIMEText
import requests

# Load environment variables from .env file if it exists
load_dotenv()


# ==============================
# Centralized Configuration
def get_config():
    return {
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "smtp_user": os.getenv("SMTP_USER"),
        "smtp_pass": os.getenv("SMTP_PASS"),
        "from_email": os.getenv("FROM_EMAIL"),
        "to_email": os.getenv("TO_EMAIL", ""),  # Empty default
        "meds_file": os.getenv("MEDS_FILE", "meds.json"),
        "fda_api_key": os.getenv("FDA_API_KEY", "")  # Optional
    }


# Get configuration
config = get_config()

# ==============================
# Config and Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE = config["meds_file"]

# Initialize session state for user email
if 'user_email' not in st.session_state:
    st.session_state.user_email = config["to_email"]


# ==============================
# Data Handling
def load_meds():
    try:
        with open(FILE, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Meds file not found or invalid; returning empty list.")
        return []


def save_meds(meds):
    try:
        with open(FILE, "w") as f:
            json.dump(meds, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving meds: {e}")
        st.error("Failed to save medications. Check logs.")


# ==============================
# Interaction Checker (with fuzzy matching) - COMPREHENSIVE VERSION
common_interactions = {
    # [Keep the same comprehensive interactions dictionary from before]
    # ... (all your interaction entries)
}


def check_interaction(d1, d2, threshold=80):
    d1_lower = d1.lower()
    d2_lower = d2.lower()
    for (key1, key2), value in common_interactions.items():
        if (fuzz.ratio(d1_lower, key1) > threshold and fuzz.ratio(d2_lower, key2) > threshold) or \
                (fuzz.ratio(d1_lower, key2) > threshold and fuzz.ratio(d2_lower, key1) > threshold):
            return value

    # If not found in static database, try FDA API if available
    if config["fda_api_key"]:
        try:
            result = check_fda_interaction(d1, d2)
            if result:
                return f"FDA data: {result}"
        except Exception as e:
            logger.warning(f"FDA API check failed: {e}")

    return None  # Return None if no interaction found


def check_fda_interaction(drug1, drug2):
    """Check for interactions using FDA API"""
    try:
        url = f"https://api.fda.gov/drug/label.json?api_key={config['fda_api_key']}&search=interactions:{drug1.lower()}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if 'results' in data:
            for result in data['results']:
                if 'drug_interactions' in result:
                    for interaction in result['drug_interactions']:
                        if drug2.lower() in interaction.lower():
                            return interaction
    except Exception as e:
        logger.error(f"FDA API error: {e}")

    return None


# ==============================
# Email Notifier
def send_email(to, subject, body):
    # Check if email is configured
    if not all([config["smtp_server"], config["smtp_user"], config["smtp_pass"], config["from_email"], to]):
        logger.warning("Email configuration incomplete. Cannot send email.")
        return False

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config["from_email"]
        msg['To'] = to

        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["smtp_user"], config["smp_pass"])
            server.send_message(msg)
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


# ==============================
# Reminder System
def remind(med):
    # Use the user's email from session state
    to_email = st.session_state.user_email
    if not to_email:
        logger.warning("No email configured for reminders")
        return

    subject = f"Medication Reminder: {med['med_name']}"
    body = f"Time to take {med['med_amt']} {med['med_name']} at {med['med_time']}.\n"
    if med['diet_restrictions']:
        body += f"Remember: Avoid {med['diet_restrictions']}."

    if send_email(to_email, subject, body):
        logger.info(f"Reminder sent for {med['med_name']} to {to_email}")
    else:
        logger.warning(f"Failed to send reminder for {med['med_name']}")


scheduler = BackgroundScheduler()
scheduler.start()


def schedule_reminders(meds):
    scheduler.remove_all_jobs()  # Clear existing jobs
    for med in meds:
        try:
            time_str = med['med_time']
            job_time = datetime.strptime(time_str, "%H:%M").time()
            scheduler.add_job(remind, 'cron', args=[med], hour=job_time.hour, minute=job_time.minute)
        except ValueError:
            logger.warning(f"Invalid time format for {med['med_name']}: {time_str}")


# Initial load and schedule
meds = load_meds()
schedule_reminders(meds)

# ==============================
# Streamlit UI
st.title("💊 Medication Tracker")

# Initialize session state for interaction checking preference
if 'check_interactions' not in st.session_state:
    st.session_state.check_interactions = False

# Check email configuration status
email_configured = all([config["smtp_server"], config["smtp_user"], config["smtp_pass"], config["from_email"]])

# Settings sidebar
with st.sidebar:
    st.header("Settings")

    # User email configuration
    st.subheader("Notification Settings")
    user_email = st.text_input(
        "Your email for notifications",
        value=st.session_state.user_email,
        placeholder="your.email@example.com"
    )

    if user_email and user_email != st.session_state.user_email:
        st.session_state.user_email = user_email
        st.success(f"Notifications will be sent to {user_email}")

    # Interaction checking toggle
    st.subheader("Medication Safety")
    st.session_state.check_interactions = st.toggle(
        "Check for medication interactions",
        value=st.session_state.check_interactions,
        help="Enable to check for potential interactions between medications"
    )

    # Display configuration status
    if st.session_state.check_interactions:
        st.info("🔍 Interaction checking is enabled")
    else:
        st.info("⚡ Interaction checking is disabled")

    if email_configured and st.session_state.user_email:
        st.success("✓ Email reminders enabled")
    elif email_configured and not st.session_state.user_email:
        st.warning("⚠️ Email configured but no recipient set")
    else:
        st.warning("✗ Email reminders disabled - configure SMTP settings")

    if config["fda_api_key"]:
        st.info("✓ FDA API enabled")
    else:
        st.info("ℹ️ FDA API not configured - using local database only")

# --- Add Meds Form ---
with st.form("add_med"):
    st.subheader("Add New Medication")

    med_name = st.text_input("Medication name*", placeholder="e.g., Warfarin, Atorvastatin")
    med_amt = st.number_input("Number of pills*", min_value=1, step=1, value=1)
    med_time = st.time_input("Time (HH:MM, 24h)*", value=datetime.now().time())
    diet_restrictions = st.text_input("Diet Restrictions", placeholder="e.g., avoid grapefruit, alcohol")

    submitted = st.form_submit_button("Add Medication")

    if submitted:
        if not med_name:
            st.error("Please enter a medication name")
        else:
            new_med = {
                "med_name": med_name,
                "med_amt": med_amt,
                "med_time": med_time.strftime("%H:%M"),
                "diet_restrictions": diet_restrictions
            }

            # Check interactions if enabled
            if st.session_state.check_interactions:
                interactions = []
                for existing_med in meds:
                    interaction = check_interaction(new_med['med_name'], existing_med['med_name'])
                    if interaction:
                        interactions.append(f"⚠️ Interaction with {existing_med['med_name']}: {interaction}")

                if interactions:
                    st.warning("### Potential Interactions Found")
                    for interaction in interactions:
                        st.write(interaction)

                    # Ask for confirmation
                    confirm = st.checkbox("I understand the risks and want to add this medication anyway")
                    if not confirm:
                        st.stop()  # Stop execution if not confirmed
                else:
                    st.success("✅ No known interactions with existing medications.")

            # Add medication to list
            meds.append(new_med)
            save_meds(meds)
            schedule_reminders(meds)  # Reschedule
            st.success(f"Added {med_name} @ {med_time.strftime('%H:%M')}")
            st.rerun()

# --- Display Meds ---
st.subheader("Your Medications")
if meds:
    for idx, med in enumerate(meds):
        col1, col2, col3 = st.columns([5, 2, 1])
        with col1:
            st.write(f"💊 **{med['med_name']}**")
            st.caption(f"Amount: {med['med_amt']} pill(s) | Time: {med['med_time']}")
            if med['diet_restrictions']:
                st.caption(f"Restrictions: {med['diet_restrictions']}")

        with col2:
            if st.session_state.check_interactions:
                # Check interactions for this specific medication
                med_interactions = []
                for other_idx, other_med in enumerate(meds):
                    if idx != other_idx:
                        interaction = check_interaction(med['med_name'], other_med['med_name'])
                        if interaction:
                            med_interactions.append(f"With {other_med['med_name']}: {interaction}")

                if med_interactions:
                    with st.popover("⚠️ Interactions"):
                        for interaction in med_interactions:
                            st.write(interaction)

        with col3:
            if st.button("❌ Remove", key=f"del{idx}"):
                meds.pop(idx)
                save_meds(meds)
                schedule_reminders(meds)  # Reschedule
                st.success(f"Removed {med['med_name']}")
                st.rerun()
else:
    st.info("No medications added yet. Use the form above to add your first medication.")

# --- Timetable ---
st.subheader("📅 Medication Timetable")
if meds:
    timetable = sorted(meds, key=lambda m: m['med_time'])

    # Create a formatted table
    timetable_data = []
    for m in timetable:
        timetable_data.append({
            "Medication": m['med_name'],
            "Time": m['med_time'],
            "Amount": f"{m['med_amt']} pill(s)",
            "Restrictions": m['diet_restrictions'] or "None"
        })

    st.dataframe(timetable_data, use_container_width=True)

    # Also show a visual timeline
    st.subheader("🕒 Daily Schedule")
    for m in timetable:
        st.write(f"**{m['med_time']}** - {m['med_amt']} {m['med_name']}")
else:
    st.info("No medications scheduled yet.")

# --- Interaction Report ---
if st.session_state.check_interactions and meds:
    st.subheader("📋 Interaction Report")

    all_interactions = []
    for i, med1 in enumerate(meds):
        for j, med2 in enumerate(meds):
            if i < j:  # Avoid duplicate checks
                interaction = check_interaction(med1['med_name'], med2['med_name'])
                if interaction:
                    all_interactions.append({
                        "Medication 1": med1['med_name'],
                        "Medication 2": med2['med_name'],
                        "Interaction": interaction
                    })

    if all_interactions:
        for interaction in all_interactions:
            with st.expander(f"⚠️ {interaction['Medication 1']} + {interaction['Medication 2']}"):
                st.warning(interaction['Interaction'])
    else:
        st.success("No potential interactions found among your medications.")

# Test notification button
if email_configured and st.session_state.user_email:
    if st.sidebar.button("Test Notification"):
        test_subject = "Test Notification from Medication Tracker"
        test_body = "This is a test notification to confirm your email settings are working correctly."
        if send_email(st.session_state.user_email, test_subject, test_body):
            st.sidebar.success("Test notification sent successfully!")
        else:
            st.sidebar.error("Failed to send test notification. Check your SMTP settings.")