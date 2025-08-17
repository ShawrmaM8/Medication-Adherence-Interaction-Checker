import json, time, threading, requests
import streamlit as st

# ==============================
# Data file
FILE = r"C:\Users\muzam\OneDrive\Desktop\PROJECTS\medication-adherence&interaction-checker\meds.json"


def load_meds():
    try:
        with open(FILE) as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except FileNotFoundError:
        return []

def save_meds(meds):
    with open(FILE, "w") as f:
        json.dump(meds, f, indent=2)

# ==============================
# Interaction dictionary
common_interactions = {
    ("ibuprofen", "aspirin"): "Both are NSAIDs → risk of stomach bleeding",
    ("atorvastatin", "grapefruit"): "Grapefruit inhibits CYP3A4 → ↑ atorvastatin levels & side effects",
    ("warfarin", "leafy greens"): "Vitamin K in leafy greens reduces warfarin effectiveness",
    ("metformin", "alcohol"): "Increased risk of lactic acidosis",
    ("ciprofloxacin", "tizanidine"): "↑ Tizanidine levels → hypotension",
    ("simvastatin", "grapefruit"): "↑ Simvastatin levels → risk of rhabdomyolysis",
    ("warfarin", "aspirin"): "↑ bleeding risk (both anticoagulants)",
    ("omeprazole", "clopidogrel"): "Omeprazole reduces clopidogrel activation",
    ("alcohol", "metronidazole"): "Disulfiram-like reaction (nausea/vomiting)",
    ("st. john's wort", "antidepressants"): "Risk of serotonin syndrome",
    ("grapefruit juice", "statins"): "↑ statin levels → side effects",
    ("caffeine", "theophylline"): "↑ theophylline levels → toxicity"
}

def check_interaction(d1, d2):
    pair = (d1.lower(), d2.lower())
    rev = (d2.lower(), d1.lower())
    if pair in common_interactions:
        return common_interactions[pair]
    if rev in common_interactions:
        return common_interactions[rev]
    return "✅ No known interaction in our database"

# ==============================
# Reminder system
def remind(med):
    st.toast(f"⏰ Reminder: Take {med['med_amt']} {med['med_name']} at {med['med_time']}")

def scheduler_loop():
    while True:
        meds = load_meds()
        now = time.strftime("%H:%M")
        for med in meds:
            if str(med["med_time"])[:5] == now:  # compare HH:MM only
                remind(med)
        time.sleep(60)

threading.Thread(target=scheduler_loop, daemon=True).start()

# ==============================
# Streamlit UI
st.title("💊 Medication Tracker")

meds = load_meds()

# --- Add meds ---
with st.form("add_med"):
    med_name = st.text_input("Medication name")
    med_amt = st.number_input("Number of pills", min_value=1, step=1)
    med_time = st.time_input("Time (HH:MM, 24h)")
    med_date = st.date_input("Date")
    submitted = st.form_submit_button("Add")
    if submitted and med_name:
        meds.append({
            "med_name": med_name,
            "med_amt": med_amt,
            "med_time": med_time.strftime("%H:%M"),
            "med_date": str(med_date)
        })
        save_meds(meds)
        st.success(f"Added {med_name} @ {med_time}")
        st.rerun()

# --- Display meds ---
st.subheader("Your medications")
if meds:
    for idx, med in enumerate(meds):
        col1, col2 = st.columns([4,1])
        col1.write(f"💊 {med['med_amt']} **{med['med_name']}** @ **{med['med_time']}** on {med['med_date']}")
        if col2.button("❌ Remove", key=f"del{idx}"):
            meds.pop(idx)
            save_meds(meds)
            st.warning(f"Removed {med['med_name']}")
            st.rerun()
else:
    st.info("No medications added yet.")

# --- Interaction checker ---
st.subheader("🔎 Drug Interaction Checker")
all_drugs = sorted(set([d for pair in common_interactions.keys() for d in pair]))
drug1 = st.selectbox("Select first drug", all_drugs, key="d1")
drug2 = st.selectbox("Select second drug", all_drugs, key="d2")

if st.button("Check Interaction"):
    result = check_interaction(drug1, drug2)
    if "✅" in result:
        st.success(result)
    else:
        st.error(result)
