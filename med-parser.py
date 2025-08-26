# Purpose: NLP-ish drug name extraction

import re

def extract_med_from_text(text):
    meds = re.findall(r'\b([A-Z][a-z]+(?:statin|ol|ine|pril|mab))\b', text)
    return meds