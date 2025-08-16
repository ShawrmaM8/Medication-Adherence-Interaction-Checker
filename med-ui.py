import json, streamlit as st

file =  r"C:\Users\muzam\OneDrive\Desktop\PROJECTS\medication-adherence&interaction-checker\meds.json"

def load_meds():
    try:
        with open(file) as f:
            content = f.read().strip() # In case file is empty, return []
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    
def save_meds(meds):
    with open(file, 'w') as f:
        json.dump(meds, f, indent=2)
        
meds = load_meds()

# --- Normalize old data (convert "name"/"time" → "med_name"/"med_time") ---
for med in meds:
    if "name" in med and "time" in med:
        med["med_name"] = med.pop("name")
        med["med_time"] = med.pop("time")
save_meds(meds)  # Save back normalized data

st.title('💊 Medication Tracker')

# --- Add new medication ---
with st.form('add_med'):
    med_name = st.text_input('Medication Name')
    med_amt = st.number_input('Number of Pills')
    med_time = st.time_input('Time (HH:MM:SS) [24h]')
    med_date = st.date_input('Date (YYYY-MM-DD)')
    med_submitted = st.form_submit_button("Add")
    
    if med_submitted and med_name and med_amt and med_time and med_date:
        meds.append({'med_name': med_name, 'med_amt': med_amt, 'med_time': med_time, 'med_date': med_date})
        save_meds(meds)
        st.success("Info added!")
        
# --- Display & delete meds ---
st.subheader("Your medications")

if meds:
    for idx, med in enumerate(meds): # enumerate assigns counter as it iterates over a list, returning idx and value pairs (json)
        
        col1, col2 = st.columns([3,1])
        col1.write(f"💊 You took {med_amt} **{med_name}(s)** @ **{med_time}** on {med_date}")
                
        if col2.button("❌ Remove", key=f"del{idx}"):
            meds.pop(idx)
            save_meds(meds)
            st.warning(f"Removed {med['med_name']}")
            st.rerun()

else:
    st.info("No medications added yet.")

