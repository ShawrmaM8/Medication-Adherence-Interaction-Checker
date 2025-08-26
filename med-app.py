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

load_dotenv()  # Load environment variables

# ==============================
# Config and Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FILE = os.getenv("MEDS_FILE", "meds.json")  # Default to meds.json if not set

# Email config from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = os.getenv("TO_EMAIL")

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
    ("ibuprofen", "aspirin"): "Both are NSAIDs → risk of stomach bleeding",
    ("atorvastatin", "grapefruit"): "Grapefruit inhibits CYP3A4, which may increase atorvastatin levels → risk of side effects like stomach damage",
    ("warfarin", "leafy greens"): "high vitamin K content in leafy greens can reduce warfarin effectiveness",
    ("metformin", "alcohol"): "increased risk of lactic acidosis when combined with alcohol",
    ("MAOI", "Aged Meats"): "High tyramine levels can cause hypertensive crisis",
    ("Digoxin", "Macrolide"): "Increased Digoxin levels lead to toxicity",
    ("Ciprofloxacin", "Tizanidine"): "Ciprofloxacin inhibits CYP1A2, increasing tizanidine levels and risk of hypotension",
    ("Simvastatin", "Grapefruit"): "Grapefruit inhibits CYP3A4, increasing simvastatin levels & risk of rhabdomyolysis",
    ("Rifampin", "Oral Contraceptives"): "Rifampin reduces CYP enzymes, reducing contraceptive effectiveness",
    ("st. john's wort", "antiretrovirals"): "Induces CYP3A4, decreasing antiretroviral drug levels",
    ("ginkgo biloba", "anticoagulants"): "Increased risk of bleeding due to antiplatelet effects",
    ("vitamin k", "warfarin"): "Vitamin K antagonizes warfarin's anticoagulant effect",
    ("iron", "levothyroxine"): "Iron supplements can reduce levothyroxine absorption",
    ("calcium", "antibiotics"): "Calcium can bind to antibiotics like tetracyclines, reducing their absorption",
    ("caffeine", "theophylline"): "Caffeine can increase theophylline levels, leading to toxicity",
    ("alcohol", "antihistamines"): "Increased sedative effects, leading to drowsiness",
    ("nsaids", "lithium"): "Increased lithium levels, risk of toxicity",
    ("antacids", "iron supplements"): "Antacids can decrease iron absorption",
    ("warfarin", "aspirin"): "Increased bleeding risk due to combined anticoagulant effects",
    ("ace inhibitors", "potassium supplements"): "Risk of hyperkalemia due to potassium retention",
    ("diuretics", "lithium"): "Diuretics can increase lithium levels, leading to toxicity",
    ("antidepressants", "alcohol"): "Increased risk of side effects and sedation",
    ("antibiotics", "oral contraceptives"): "Some antibiotics can reduce contraceptive effectiveness",
    ("grapefruit juice", "statins"): "Grapefruit juice inhibits CYP3A4, increasing statin levels and risk of side effects",
    ("cimetidine", "warfarin"): "Cimetidine inhibits warfarin metabolism, increasing bleeding risk",
    ("omeprazole", "clopidogrel"): "Omeprazole inhibits CYP2C19, reducing clopidogrel activation",
    ("grapefruit juice", "calcium channel blockers"): "Increased calcium channel blocker levels, risk of hypotension",
    ("alcohol", "metronidazole"): "Disulfiram-like reaction causing nausea and vomiting",
    ("ginseng", "anticoagulants"): "Ginseng may reduce the effectiveness of anticoagulants",
    ("licorice", "diuretics"): "Licorice can cause potassium loss, increasing diuretic effects",
    ("grapefruit juice", "benzodiazepines"): "Increased benzodiazepine levels, risk of sedation",
    ("caffeine", "antipsychotics"): "Caffeine can reduce the effectiveness of antipsychotic medications",
    ("st. john's wort", "antidepressants"): "Risk of serotonin syndrome when combined with SSRIs",
    ("vitamin e", "warfarin"): "Increased bleeding risk due to anticoagulant effects",
    ("grapefruit juice", "immunosuppressants"): "Increased immunosuppressant levels, risk of toxicity",
    ("aspirin", "methotrexate"): "Increased methotrexate levels, risk of toxicity",
    ("ciprofloxacin", "warfarin"): "Ciprofloxacin can enhance warfarin's anticoagulant effect",
    ("antacids", "digoxin"): "Antacids can decrease digoxin absorption",
    ("furosemide", "lithium"): "Increased lithium levels due to decreased renal clearance",
    ("cimetidine", "theophylline"): "Cimetidine inhibits theophylline metabolism, increasing levels",
    ("grapefruit juice", "buspirone"): "Increased buspirone levels, risk of side effects",
    ("warfarin", "alcohol"): "Alcohol can enhance warfarin's anticoagulant effect",
    ("methotrexate", "nsaids"): "Increased methotrexate levels, risk of toxicity",
    ("verapamil", "beta-blockers"): "Increased risk of bradycardia and heart block",
    ("grapefruit juice", "tacrolimus"): "Increased tacrolimus levels, risk of toxicity"
}

def check_interaction(d1, d2, threshold=80):
    d1_lower = d1.lower()
    d2_lower = d2.lower()
    for (key1, key2), value in common_interactions.items():
        if (fuzz.ratio(d1_lower, key1) > threshold and fuzz.ratio(d2_lower, key2) > threshold) or \
           (fuzz.ratio(d1_lower, key2) > threshold and fuzz.ratio(d2_lower, key1) > threshold):
            return value
    return None  # Return None if no interaction found

# ==============================
# Email Notifier
def send_email(to, subject, body):
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

# ==============================
# Reminder System
def remind(med):
    subject = f"Medication Reminder: {med['med_name']}"
    body = f"Time to take {med['med_amt']} {med['med_name']} at {med['med_time']}.\n"
    if med['diet_restrictions']:
        body += f"Remember: Avoid {med['diet_restrictions']}."
    send_email(TO_EMAIL, subject, body)
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
    diet_restrictions = st.text_input("Diet Restrictions (e.g., avoid grapefruit, alcohol)")
    submitted = st.form_submit_button("Add")
    if submitted and med_name:
        new_med = {
            "med_name": med_name,
            "med_amt": med_amt,
            "med_time": med_time.strftime("%H:%M"),
            "diet_restrictions": diet_restrictions
        }
        # Check interactions with existing meds
        interactions = []
        for existing_med in meds:
            interaction = check_interaction(new_med['med_name'], existing_med['med_name'])
            if interaction:
                interactions.append(f"Interaction with {existing_med['med_name']}: {interaction}")
        if interactions:
            st.warning("Potential interactions found:\n" + "\n".join(interactions))
        else:
            st.success("✅ No known interactions with existing medications.")
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
        col1.write(f"💊 {med['med_amt']} **{med['med_name']}** @ **{med['med_time']}** | Restrictions: {med['diet_restrictions']}")
        if col2.button("❌ Remove", key=f"del{idx}"):
            meds.pop(idx)
            save_meds(meds)
            schedule_reminders(meds)  # Reschedule
            st.warning(f"Removed {med['med_name']}")
            st.rerun()
else:
    st.info("No medications added yet.")

# --- Timetable ---
st.subheader("📅 Medication Timetable")
if meds:
    timetable = sorted(meds, key=lambda m: m['med_time'])
    st.table([{"Name": m['med_name'], "Time": m['med_time'], "Amount": m['med_amt'], "Restrictions": m['diet_restrictions']} for m in timetable])