import json
import time
import threading
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from fuzzywuzzy import fuzz
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

# ==============================
# Config and Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE = os.getenv("MEDS_FILE", "meds.json")  # Default to meds.json if not set

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
# Interaction Checker (with fuzzy matching)
common_interactions = {
    # (Existing dict here; omitted for brevity)
}

def check_interaction(d1, d2, threshold=80):
    d1_lower = d1.lower()
    d2_lower = d2.lower()
    for (key1, key2), value in common_interactions.items():
        if (fuzz.ratio(d1_lower, key1) > threshold and fuzz.ratio(d2_lower, key2) > threshold) or \
           (fuzz.ratio(d1_lower, key2) > threshold and fuzz.ratio(d2_lower, key1) > threshold):
            return value
    return "✅ No known interaction in our database"

# ==============================
# Reminder System
def remind(med):
    st.toast(f"⏰ Reminder: Take {med['med_amt']} {med['med_name']} at {med['med_time']}")
    logger.info(f"Reminder sent for {med['med_name']}")

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

# --- Add Meds Form ---
with st.form("add_med"):
    med_name = st.text_input("Medication name")
    med_amt = st.number_input("Number of pills", min_value=1, step=1)
    med_time = st.time_input("Time (HH:MM, 24h)")
    med_date = st.date_input("Date")
    diet_restrictions = st.text_input("Diet Restrictions")
    submitted = st.form_submit_button("Add")
    if submitted and med_name:
        new_med = {
            "med_name": med_name,
            "med_amt": med_amt,
            "med_time": med_time.strftime("%H:%M"),
            "med_date": str(med_date),
            "diet_restrictions": diet_restrictions
        }
        meds.append(new_med)
        save_meds(meds)
        schedule_reminders(meds)  # Reschedule
        st.success(f"Added {med_name} @ {med_time.strftime('%H:%M')}")
        st.rerun()

# --- Display Meds ---
st.subheader("Your Medications")
if meds:
    for idx, med in enumerate(meds):
        col1, col2 = st.columns([4, 1])
        col1.write(f"💊 {med['med_amt']} **{med['med_name']}** @ **{med['med_time']}** on {med['med_date']}")
        if col2.button("❌ Remove", key=f"del{idx}"):
            meds.pop(idx)
            save_meds(meds)
            schedule_reminders(meds)  # Reschedule
            st.warning(f"Removed {med['med_name']}")
            st.rerun()
else:
    st.info("No medications added yet.")

# --- Interaction Checker ---
st.subheader("🔎 Drug Interaction Checker")
all_drugs = sorted(set(d for pair in common_interactions for d in pair))
drug1 = st.selectbox("Select first drug", all_drugs, key="d1")
drug2 = st.selectbox("Select second drug", all_drugs, key="d2")

if st.button("Check Interaction"):
    result = check_interaction(drug1, drug2)
    if "✅" in result:
        st.success(result)
    else:
        st.error(result)

# --- Timetable ---
st.subheader("📅 Medication Timetable")
# (Add a simple table view if desired, e.g., using st.dataframe)
if meds:
    timetable = sorted(meds, key=lambda m: m['med_time'])
    st.table([{"Name": m['med_name'], "Time": m['med_time'], "Date": m['med_date'], "Amount": m['med_amt']} for m in timetable])

