"""
Medical Pharmacology & Lab Reference Knowledge Base
Author: Clinical Governance & Pharmacology Board

Provides clinically validated reference data for:
- Detecting medicines from prescription notes, images, and text
- Mapping active molecules to primary underlying diseases/conditions
- Identifying direct therapeutic equivalents (medicines that do the exact same work)
- Interpreting lab report values (HbA1c, Lipids, CBC, Liver/Kidney/Thyroid)
- Generating draft prescription summaries for clinician sign-off
"""

import re

# Comprehensive Clinical Pharmacology Reference Database
MEDICINE_DATABASE = {
    "metformin": {
        "generic_name": "Metformin Hydrochloride",
        "aliases": ["metformin", "glycomet", "glucophage", "obimet", "riomet"],
        "primary_disease": "Type 2 Diabetes Mellitus / Insulin Resistance",
        "therapeutic_class": "Biguanide Antidiabetic Agent",
        "mechanism_of_action": "Reduces hepatic glucose production, decreases intestinal absorption of glucose, and improves insulin sensitivity by increasing peripheral glucose uptake and utilization.",
        "standard_dosage": "500 mg or 850 mg orally with or after meals twice daily",
        "formulation": "Tablet (Immediate or Extended Release)",
        "equivalent_alternatives": [
            {
                "name": "Glimepiride",
                "class": "Sulfonylurea",
                "how_it_works": "Stimulates beta cells in the pancreas to release more natural insulin.",
                "typical_use": "Often prescribed alongside or as alternative when glycemic targets require insulin secretagogue action."
            },
            {
                "name": "Vildagliptin / Sitagliptin",
                "class": "DPP-4 Inhibitor",
                "how_it_works": "Inhibits DPP-4 enzyme, increasing active incretin hormones that stimulate post-meal insulin release.",
                "typical_use": "Low hypoglycemia risk alternative or combination with Metformin."
            },
            {
                "name": "Dapagliflozin / Empagliflozin",
                "class": "SGLT2 Inhibitor",
                "how_it_works": "Filters excess blood glucose out through urine via renal proximal tubules.",
                "typical_use": "Provides renal and cardiovascular protective glycemic control."
            }
        ]
    },
    "atorvastatin": {
        "generic_name": "Atorvastatin Calcium",
        "aliases": ["atorvastatin", "atorva", "lipitor", "atorlip", "tonact", "storvas"],
        "primary_disease": "Hypercholesterolemia / Dyslipidemia & Cardiovascular Risk Prevention",
        "therapeutic_class": "HMG-CoA Reductase Inhibitor (Statin)",
        "mechanism_of_action": "Competitively inhibits HMG-CoA reductase, the rate-limiting enzyme in hepatic cholesterol synthesis, substantially lowering LDL ('bad') cholesterol and triglycerides while raising HDL.",
        "standard_dosage": "10 mg to 20 mg once daily at bedtime",
        "formulation": "Film-coated Tablet",
        "equivalent_alternatives": [
            {
                "name": "Rosuvastatin",
                "class": "High-intensity Statin",
                "how_it_works": "Highly potent HMG-CoA reductase inhibitor with hydrophilic profile; often causes fewer muscle aches.",
                "typical_use": "Direct equivalent with comparable or greater LDL-lowering efficacy at lower mg doses (e.g. 5-10 mg)."
            },
            {
                "name": "Simvastatin",
                "class": "Moderate-intensity Statin",
                "how_it_works": "Lowers hepatic cholesterol synthesis and increases clearance of circulating LDL.",
                "typical_use": "Standard maintenance alternative for lipid control."
            },
            {
                "name": "Pitavastatin",
                "class": "Statin",
                "how_it_works": "Inhibits cholesterol synthesis with minimal cytochrome P450 drug-drug interactions.",
                "typical_use": "Ideal for patients on polypharmacy or with mild statin intolerance."
            }
        ]
    },
    "amlodipine": {
        "generic_name": "Amlodipine Besylate",
        "aliases": ["amlodipine", "amlong", "stamlo", "norvasc", "amlopres"],
        "primary_disease": "Essential Hypertension & Chronic Stable Angina",
        "therapeutic_class": "Dihydropyridine Calcium Channel Blocker (CCB)",
        "mechanism_of_action": "Relaxes vascular smooth muscle by selectively inhibiting calcium ion influx across cell membranes, resulting in arterial vasodilation and decreased peripheral vascular resistance.",
        "standard_dosage": "5 mg once daily, titratable to 10 mg",
        "formulation": "Tablet",
        "equivalent_alternatives": [
            {
                "name": "Cilnidipine",
                "class": "Dual L/N-type Calcium Channel Blocker",
                "how_it_works": "Blocks both vascular L-type and sympathetic N-type calcium channels, dilating arterioles without reflex tachycardia or ankle edema.",
                "typical_use": "Direct equivalent often preferred if patient experiences pedal edema (swollen feet) on Amlodipine."
            },
            {
                "name": "Nifedipine (Extended Release)",
                "class": "Dihydropyridine CCB",
                "how_it_works": "Potent peripheral arteriolar vasodilator providing sustained 24-hour blood pressure reduction.",
                "typical_use": "Direct pharmacological class alternative."
            },
            {
                "name": "S-Amlodipine",
                "class": "Chiral Single Enantiomer CCB",
                "how_it_works": "Contains only the therapeutically active S-enantiomer, offering effective blood pressure reduction at half the dose (2.5 mg) with lower side effects.",
                "typical_use": "Direct equivalent with reduced ankle swelling."
            }
        ]
    },
    "telmisartan": {
        "generic_name": "Telmisartan",
        "aliases": ["telmisartan", "telma", "micardis", "telvas", "telsartan"],
        "primary_disease": "Hypertension & Cardiovascular Risk Reduction",
        "therapeutic_class": "Angiotensin II Receptor Blocker (ARB)",
        "mechanism_of_action": "Selectively blocks the binding of angiotensin II to AT1 receptors in vascular smooth muscle and adrenal gland, blocking vasoconstriction and aldosterone secretion.",
        "standard_dosage": "40 mg once daily orally",
        "formulation": "Tablet",
        "equivalent_alternatives": [
            {
                "name": "Losartan",
                "class": "Angiotensin Receptor Blocker (ARB)",
                "how_it_works": "Blocks AT1 angiotensin receptors, preventing arterial constriction and lowering systemic blood pressure.",
                "typical_use": "Direct pharmacological equivalent; also promotes renal uric acid excretion."
            },
            {
                "name": "Olmesartan",
                "class": "Angiotensin Receptor Blocker (ARB)",
                "how_it_works": "Potent and selective AT1 blocker providing prolonged 24-hour hemodynamic control.",
                "typical_use": "Direct therapeutic equivalent for resistant hypertension."
            },
            {
                "name": "Valsartan",
                "class": "Angiotensin Receptor Blocker (ARB)",
                "how_it_works": "Selectively antagonizes angiotensin II mediated vasoconstriction with strong cardioprotective evidence.",
                "typical_use": "Direct equivalent for hypertension and post-myocardial infarction care."
            }
        ]
    },
    "omeprazole": {
        "generic_name": "Omeprazole",
        "aliases": ["omeprazole", "omez", "prilosec", "omizac", "losec"],
        "primary_disease": "Gastroesophageal Reflux Disease (GERD) & Peptic Ulcer Disease",
        "therapeutic_class": "Proton Pump Inhibitor (PPI)",
        "mechanism_of_action": "Irreversibly inhibits the gastric parietal H+/K+ ATPase enzyme system ('proton pump'), suppressing both basal and stimulated gastric acid secretion.",
        "standard_dosage": "20 mg orally once daily 30-60 minutes before breakfast",
        "formulation": "Delayed-release Capsule / Tablet",
        "equivalent_alternatives": [
            {
                "name": "Pantoprazole",
                "class": "Proton Pump Inhibitor (PPI)",
                "how_it_works": "Suppresses gastric acid production with lower affinity for hepatic CYP2C19, reducing drug-drug interaction risk.",
                "typical_use": "Direct equivalent; standard first-line alternative (40 mg before breakfast)."
            },
            {
                "name": "Rabeprazole",
                "class": "Proton Pump Inhibitor (PPI)",
                "how_it_works": "Rapid-onset gastric acid suppression offering prompt relief of acid reflux and heartburn.",
                "typical_use": "Direct equivalent (20 mg once daily)."
            },
            {
                "name": "Esomeprazole",
                "class": "S-enantiomer PPI",
                "how_it_works": "Provides higher systemic bioavailability and sustained intragastric pH control above 4.0.",
                "typical_use": "Direct equivalent with high efficacy for erosive esophagitis."
            }
        ]
    },
    "paracetamol": {
        "generic_name": "Acetaminophen / Paracetamol",
        "aliases": ["paracetamol", "acetaminophen", "dolo", "crocin", "calpol", "tylenol", "panadol", "pacimol"],
        "primary_disease": "Fever (Pyrexia) & Mild-to-Moderate Pain (Headache, Bodyache, Myalgia)",
        "therapeutic_class": "Analgesic & Antipyretic",
        "mechanism_of_action": "Inhibits central prostaglandin synthesis in the brain and modulates the hypothalamic heat-regulating center to promote heat dissipation through peripheral vasodilation and sweating.",
        "standard_dosage": "500 mg to 650 mg orally every 4 to 6 hours as needed (Maximum 3000 mg/day)",
        "formulation": "Tablet / Syrup",
        "equivalent_alternatives": [
            {
                "name": "Ibuprofen",
                "class": "NSAID",
                "how_it_works": "Inhibits COX-1 and COX-2 enzymes to deliver both anti-inflammatory and pain-relieving effects.",
                "typical_use": "Preferred when musculoskeletal swelling or inflammatory joint pain accompanies fever."
            },
            {
                "name": "Naproxen",
                "class": "Long-acting NSAID",
                "how_it_works": "Provides extended 12-hour pain relief and anti-inflammatory coverage.",
                "typical_use": "Convenient twice-daily alternative for sustained pain relief."
            }
        ]
    },
    "amoxicillin": {
        "generic_name": "Amoxicillin (+/- Clavulanic Acid)",
        "aliases": ["amoxicillin", "augmentin", "moxikind", "mox", "novamox", "clamox"],
        "primary_disease": "Bacterial Respiratory, Sinus, Dental, or Urinary Tract Infections",
        "therapeutic_class": "Broad-spectrum Aminopenicillin Antibiotic",
        "mechanism_of_action": "Binds to bacterial penicillin-binding proteins (PBPs), inhibiting the synthesis of bacterial peptidoglycan cell walls, leading to osmotic lysis and bacterial death.",
        "standard_dosage": "500 mg / 625 mg orally twice to thrice daily with meals for 5-7 days",
        "formulation": "Tablet / Dry Syrup",
        "equivalent_alternatives": [
            {
                "name": "Cefuroxime Axetil",
                "class": "Second-generation Cephalosporin",
                "how_it_works": "Resistant to many beta-lactamases; inhibits bacterial cell wall synthesis.",
                "typical_use": "Alternative for respiratory or soft tissue bacterial infections."
            },
            {
                "name": "Azithromycin",
                "class": "Macrolide Antibiotic",
                "how_it_works": "Inhibits bacterial protein synthesis by binding to the 50S ribosomal subunit.",
                "typical_use": "Convenient once-daily 3 to 5 day course; safe alternative for penicillin-allergic patients."
            }
        ]
    },
    "azithromycin": {
        "generic_name": "Azithromycin",
        "aliases": ["azithromycin", "azithral", "zithromax", "azee", "zady"],
        "primary_disease": "Bacterial Throat / Pharyngitis, Bronchitis, Pneumonia, & Soft Tissue Infections",
        "therapeutic_class": "Macrolide Antibiotic",
        "mechanism_of_action": "Blocks transpeptidation by reversibly binding to the 50S subunit of the 70S bacterial ribosome, preventing bacterial protein synthesis.",
        "standard_dosage": "500 mg orally once daily 1 hour before or 2 hours after meals for 3 to 5 days",
        "formulation": "Film-coated Tablet",
        "equivalent_alternatives": [
            {
                "name": "Clarithromycin",
                "class": "Macrolide",
                "how_it_works": "Inhibits 50S ribosomal protein translation with high tissue penetration.",
                "typical_use": "Alternative macrolide for atypical chest infections and H. pylori eradication."
            },
            {
                "name": "Doxycycline",
                "class": "Tetracycline",
                "how_it_works": "Binds to the 30S ribosomal subunit preventing access of aminoacyl-tRNA to the ribosomal acceptor site.",
                "typical_use": "Broad-spectrum alternative for respiratory, skin, and atypical bacterial pathogens."
            }
        ]
    },
    "cetirizine": {
        "generic_name": "Cetirizine Hydrochloride",
        "aliases": ["cetirizine", "cetzine", "zyrtec", "alerid", "okacet"],
        "primary_disease": "Allergic Rhinitis, Seasonal Allergies, Urticaria (Hives), & Skin Itching",
        "therapeutic_class": "Second-generation H1-Antihistamine",
        "mechanism_of_action": "Selectively competes with free histamine for binding at peripheral H1-receptor sites, preventing histamine-induced capillary dilation and itch sensation.",
        "standard_dosage": "10 mg orally once daily in the evening",
        "formulation": "Tablet / Syrup",
        "equivalent_alternatives": [
            {
                "name": "Levocetirizine",
                "class": "R-enantiomer Antihistamine",
                "how_it_works": "Contains the active R-enantiomer with twice the affinity for H1 receptors at half the dose (5 mg) and substantially less daytime sedation.",
                "typical_use": "Direct refined equivalent (e.g. 5 mg at night)."
            },
            {
                "name": "Fexofenadine",
                "class": "Non-sedating Second-gen Antihistamine",
                "how_it_works": "Does not cross the blood-brain barrier; blocks peripheral histamine receptors with virtually zero drowsiness.",
                "typical_use": "Top daytime alternative for drivers, working professionals, and students (120 mg or 180 mg)."
            },
            {
                "name": "Loratadine",
                "class": "Non-sedating Antihistamine",
                "how_it_works": "Long-acting peripheral H1 antagonist with once-daily convenience.",
                "typical_use": "Alternative for chronic allergic rhinitis."
            }
        ]
    },
    "salbutamol": {
        "generic_name": "Salbutamol / Albuterol Sulfate",
        "aliases": ["salbutamol", "albuterol", "asthalin", "ventolin", "asmacort"],
        "primary_disease": "Bronchospasm in Asthma, COPD, & Acute Wheezing",
        "therapeutic_class": "Short-acting Beta-2 Adrenergic Agonist (SABA)",
        "mechanism_of_action": "Stimulates beta-2 adrenergic receptors in bronchial smooth muscle, activating adenylate cyclase to produce cyclic AMP, resulting in rapid bronchial dilation and airway opening.",
        "standard_dosage": "100 mcg to 200 mcg (1 to 2 puffs) via inhaler as needed for acute shortness of breath",
        "formulation": "Metered Dose Inhaler (MDI) / Respules",
        "equivalent_alternatives": [
            {
                "name": "Levosalbutamol (Levalbuterol)",
                "class": "Pure (R)-enantiomer SABA",
                "how_it_works": "Excludes the inert (S)-enantiomer, providing rapid bronchodilation with significantly reduced tremors and heart palpitations.",
                "typical_use": "Direct refined equivalent (50 mcg/puff)."
            },
            {
                "name": "Formoterol (+/- Budesonide)",
                "class": "Rapid-onset LABA",
                "how_it_works": "Combines rapid bronchodilator onset with prolonged 12-hour duration of action.",
                "typical_use": "Maintenance and symptom-reliever therapy in modern SMART asthma guidelines."
            }
        ]
    },
    "levothyroxine": {
        "generic_name": "Levothyroxine Sodium",
        "aliases": ["levothyroxine", "thyronorm", "eltroxin", "synthroid", "thyrox"],
        "primary_disease": "Hypothyroidism (Underactive Thyroid Gland)",
        "therapeutic_class": "Synthetic Thyroid Hormone (T4)",
        "mechanism_of_action": "Synthetic levothyroxine is deiodinated in peripheral tissues to triiodothyronine (T3), binding to nuclear thyroid receptors to normalize basal metabolic rate, energy, and cardiovascular homeostasis.",
        "standard_dosage": "25 mcg to 100 mcg once daily in the morning on an empty stomach with plain water (30-60 min before breakfast)",
        "formulation": "Tablet",
        "equivalent_alternatives": [
            {
                "name": "Eltroxin / Thyronorm (Equivalent Brands)",
                "class": "Synthetic T4",
                "how_it_works": "Identical active synthetic T4; requires strict dose consistency and periodic TSH monitoring.",
                "typical_use": "Direct bioequivalent brand alternative with same microgram strength."
            }
        ]
    }
}

# Clinical Laboratory Test Normal Ranges & Abnormal Patterns
LAB_TEST_RANGES = {
    "hba1c": {
        "name": "Hemoglobin A1c (HbA1c)",
        "normal_range": "< 5.7 %",
        "prediabetes": "5.7 - 6.4 %",
        "diabetic": ">= 6.5 %",
        "unit": "%",
        "significance": "Reflects average blood sugar control over the past 2-3 months."
    },
    "fasting_glucose": {
        "name": "Fasting Blood Glucose",
        "normal_range": "70 - 99 mg/dL",
        "elevated": ">= 100 mg/dL",
        "unit": "mg/dL",
        "significance": "Assesses baseline insulin regulation following an 8-hour fast."
    },
    "blood_pressure": {
        "name": "Blood Pressure (Systolic / Diastolic)",
        "normal_range": "< 120 / 80 mmHg",
        "elevated": "120-129 / <80 mmHg",
        "hypertensive": ">= 130 / 80 mmHg",
        "unit": "mmHg",
        "significance": "Measurement of pressure against arterial walls."
    },
    "cholesterol": {
        "name": "Total Cholesterol",
        "normal_range": "< 200 mg/dL",
        "borderline": "200 - 239 mg/dL",
        "high": ">= 240 mg/dL",
        "unit": "mg/dL",
        "significance": "Indicator of total circulating blood lipids and cardiovascular risk."
    },
    "hemoglobin": {
        "name": "Hemoglobin (CBC)",
        "normal_range": "Male: 13.8 - 17.2 g/dL | Female: 12.1 - 15.1 g/dL",
        "low_indicator": "< 12.0 g/dL (Suggests Anemia)",
        "unit": "g/dL",
        "significance": "Oxygen-carrying capacity of red blood cells."
    },
    "tsh": {
        "name": "Thyroid Stimulating Hormone (TSH)",
        "normal_range": "0.4 - 4.5 mIU/L",
        "high_indicator": "> 4.5 mIU/L (Suggests Hypothyroidism)",
        "low_indicator": "< 0.4 mIU/L (Suggests Hyperthyroidism)",
        "unit": "mIU/L",
        "significance": "Pituitary hormone directing thyroid hormone production."
    },
    "creatinine": {
        "name": "Serum Creatinine",
        "normal_range": "0.7 - 1.3 mg/dL",
        "high_indicator": "> 1.4 mg/dL",
        "unit": "mg/dL",
        "significance": "Key marker of kidney renal filtration function."
    }
}


def detect_medicines(text: str) -> list[dict]:
    """
    Scans patient messages, OCR text, or uploaded documents to identify
    medicines, their primary diseases, mechanisms, and equivalent alternatives.
    """
    clean_text = text.lower()
    detected = []
    seen_molecules = set()

    for molecule_key, data in MEDICINE_DATABASE.items():
        for alias in data["aliases"]:
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, clean_text):
                if molecule_key not in seen_molecules:
                    seen_molecules.add(molecule_key)
                    detected.append({
                        "molecule": molecule_key,
                        "generic_name": data["generic_name"],
                        "matched_term": alias,
                        "primary_disease": data["primary_disease"],
                        "therapeutic_class": data["therapeutic_class"],
                        "mechanism_of_action": data["mechanism_of_action"],
                        "standard_dosage": data["standard_dosage"],
                        "formulation": data["formulation"],
                        "equivalent_alternatives": data["equivalent_alternatives"],
                    })
                break

    return detected


def detect_lab_reports(text: str) -> list[dict]:
    """
    Scans text for quantitative lab test mentions and flags out-of-range parameters.
    """
    clean_text = text.lower()
    findings = []

    # Check for HbA1c: e.g. "hba1c: 7.2" or "hba1c 8%"
    hba1c_match = re.search(r'hba1c[^\d]{0,10}(\d{1,2}(?:\.\d{1,2})?)', clean_text)
    if hba1c_match:
        val = float(hba1c_match.group(1))
        status = "High (Diabetic Range)" if val >= 6.5 else ("Prediabetic Range" if val >= 5.7 else "Normal")
        findings.append({
            "test_name": "Hemoglobin A1c (HbA1c)",
            "detected_value": f"{val} %",
            "reference_range": "< 5.7 %",
            "clinical_status": status,
            "interpretation": f"Your HbA1c is {val}%, which falls in the {status.lower()}."
        })

    # Check for Fasting Sugar: e.g. "fasting sugar: 145" or "glucose 110"
    fbs_match = re.search(r'(?:fasting|sugar|glucose)[^\d]{0,10}(\d{2,3})', clean_text)
    if fbs_match:
        val = int(fbs_match.group(1))
        if 50 <= val <= 500:
            status = "Elevated" if val >= 100 else "Normal"
            findings.append({
                "test_name": "Blood Glucose",
                "detected_value": f"{val} mg/dL",
                "reference_range": "70 - 99 mg/dL",
                "clinical_status": status,
                "interpretation": f"Blood glucose is {val} mg/dL ({status})."
            })

    # Check for Blood Pressure: e.g. "140/90" or "bp 130/85"
    bp_match = re.search(r'\b(\d{2,3})\s*/\s*(\d{2,3})\b', clean_text)
    if bp_match:
        sys = int(bp_match.group(1))
        dia = int(bp_match.group(2))
        if 80 <= sys <= 250 and 40 <= dia <= 150:
            status = "Hypertensive Range" if (sys >= 130 or dia >= 80) else "Optimal / Normal"
            findings.append({
                "test_name": "Blood Pressure",
                "detected_value": f"{sys}/{dia} mmHg",
                "reference_range": "< 120/80 mmHg",
                "clinical_status": status,
                "interpretation": f"Blood pressure reading of {sys}/{dia} mmHg is in the {status.lower()}."
            })

    # Check for Total Cholesterol: e.g. "cholesterol 240"
    chol_match = re.search(r'cholesterol[^\d]{0,10}(\d{2,3})', clean_text)
    if chol_match:
        val = int(chol_match.group(1))
        if 100 <= val <= 400:
            status = "High" if val >= 240 else ("Borderline Elevated" if val >= 200 else "Desirable")
            findings.append({
                "test_name": "Total Cholesterol",
                "detected_value": f"{val} mg/dL",
                "reference_range": "< 200 mg/dL",
                "clinical_status": status,
                "interpretation": f"Serum cholesterol is {val} mg/dL ({status})."
            })

    # Check for Hemoglobin: e.g. "hb: 10.5" or "hemoglobin 9.8"
    hb_match = re.search(r'(?:hemoglobin|hb)[^\d]{0,10}(\d{1,2}(?:\.\d{1,2})?)', clean_text)
    if hb_match:
        val = float(hb_match.group(1))
        if 4.0 <= val <= 20.0:
            status = "Low (Anemia Indicator)" if val < 12.0 else "Normal Range"
            findings.append({
                "test_name": "Hemoglobin (Hb)",
                "detected_value": f"{val} g/dL",
                "reference_range": "12.0 - 16.0 g/dL",
                "clinical_status": status,
                "interpretation": f"Hemoglobin count is {val} g/dL ({status})."
            })

    # Check for TSH: e.g. "tsh: 6.8"
    tsh_match = re.search(r'tsh[^\d]{0,10}(\d{1,2}(?:\.\d{1,2})?)', clean_text)
    if tsh_match:
        val = float(tsh_match.group(1))
        if 0.01 <= val <= 50.0:
            status = "Elevated (Hypothyroid Indicator)" if val > 4.5 else ("Low (Hyperthyroid Indicator)" if val < 0.4 else "Normal")
            findings.append({
                "test_name": "Thyroid Stimulating Hormone (TSH)",
                "detected_value": f"{val} mIU/L",
                "reference_range": "0.4 - 4.5 mIU/L",
                "clinical_status": status,
                "interpretation": f"Thyroid TSH value is {val} mIU/L ({status})."
            })

    return findings
