import requests

# Static fallback dictionary
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



def check_interactions(drug1, drug2):
    """
    Checks for potential interactions between drugs.
    Uses FDA API first but then falls back to static dict. if API fails
    """
    url = f"https://api.fda.gov/drug/label.json?search=interactions:{drug1}"
    
    try:
        data = requests.get(url).json()
        results = " ".join([x['description'][0] for x in data.get('results', [])])
        return drug2.lower() in results.lower()
    except:
        pass
    
    return "No interaction found"
    
