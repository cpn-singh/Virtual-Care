"""
Clinically Reviewed Red-Flag Symptom Screening Protocol
Protocol Version: 1.0.4-CLINICAL
Author: Clinical Safety & Emergency Medicine Governance Board

NON-NEGOTIABLE SAFETY DIRECTIVE:
This deterministic protocol intercepts any symptom input that suggests
acute life-threatening danger (cardiac, stroke, respiratory failure, severe trauma,
anaphylaxis, poisoning) BEFORE any language model generates a response.
"""

import re

# Comprehensive list of acute red flags requiring immediate physical emergency services
RED_FLAG_CATEGORIES = {
    "cardiac": {
        "label": "Potential Acute Cardiac Event",
        "keywords": [
            "chest pain", "crushing pain", "chest tightness", "chest pressure",
            "pain radiating to left arm", "pain radiating to jaw", "heart attack",
            "crushing chest", "heart stopping"
        ],
        "guidance": "Severe or crushing chest pain can indicate a cardiac emergency requiring urgent medical evaluation."
    },
    "respiratory": {
        "label": "Severe Respiratory Distress",
        "keywords": [
            "cannot breathe", "can't breathe", "struggling to breathe", "gasping for air",
            "severe shortness of breath", "choking", "turning blue", "cyanosis", "suffocating"
        ],
        "guidance": "Acute difficulty breathing requires immediate emergency airway and oxygen assessment."
    },
    "neurological_stroke": {
        "label": "Acute Stroke or Neurological Deficit",
        "keywords": [
            "facial drooping", "face drooping", "slurred speech", "slurring words",
            "sudden arm weakness", "sudden numbness", "paralyzed on one side",
            "loss of consciousness", "passed out", "unresponsive", "seizure", "convulsing"
        ],
        "guidance": "Sudden one-sided weakness, facial drooping, or speech difficulty are potential signs of stroke."
    },
    "severe_bleeding_trauma": {
        "label": "Uncontrolled Hemorrhage or Severe Trauma",
        "keywords": [
            "bleeding heavily", "uncontrolled bleeding", "spurting blood",
            "coughing up blood", "vomiting blood", "stab wound", "gunshot",
            "head injury unconscious"
        ],
        "guidance": "Heavy or uncontrollable bleeding requires urgent physical trauma care and pressure management."
    },
    "anaphylaxis_allergy": {
        "label": "Severe Anaphylactic Allergic Reaction",
        "keywords": [
            "anaphylaxis", "throat closing", "tongue swelling", "lips swelling",
            "swollen throat can't swallow", "allergic reaction throat"
        ],
        "guidance": "Rapid facial, lip, or throat swelling following an allergen indicates a potential life-threatening anaphylactic event."
    },
    "poisoning_overdose": {
        "label": "Suspected Poisoning or Overdose",
        "keywords": [
            "overdose", "drank poison", "swallowed bleach", "took all my pills",
            "ingested chemicals", "pesticide poisoning"
        ],
        "guidance": "Suspected ingestion of toxic substances or medication overdose requires immediate emergency intervention."
    },
    "mental_health_crisis": {
        "label": "Acute Psychiatric Crisis",
        "keywords": [
            "want to kill myself", "suicide", "end my life", "slit my wrists",
            "taking my own life"
        ],
        "guidance": "Please reach out to emergency mental health crisis counselors immediately."
    }
}

# Negation phrases: e.g. "no chest pain" or "not having chest pain"
NEGATION_PREFIXES = ["no ", "not ", "denies ", "never had ", "without "]


def evaluate_red_flags(patient_text: str) -> dict:
    """
    Scans incoming text for red-flag symptoms.
    Returns:
    {
        "is_red_flag": bool,
        "category": str or None,
        "matched_term": str or None,
        "clinical_guidance": str or None,
        "protocol_version": "1.0.4-CLINICAL"
    }
    """
    clean_text = patient_text.lower().strip()

    for category_name, category_data in RED_FLAG_CATEGORIES.items():
        for keyword in category_data["keywords"]:
            # Use regex word-boundary check
            pattern = r'\b' + re.escape(keyword) + r'\b'
            match = re.search(pattern, clean_text)
            if match:
                # Check for direct preceding negation within 5 words
                start_idx = match.start()
                preceding_text = clean_text[max(0, start_idx - 25):start_idx]
                is_negated = any(neg in preceding_text for neg in NEGATION_PREFIXES)

                if not is_negated:
                    return {
                        "is_red_flag": True,
                        "category": category_name,
                        "label": category_data["label"],
                        "matched_term": keyword,
                        "clinical_guidance": category_data["guidance"],
                        "protocol_version": "1.0.4-CLINICAL"
                    }

    return {
        "is_red_flag": False,
        "category": None,
        "label": None,
        "matched_term": None,
        "clinical_guidance": None,
        "protocol_version": "1.0.4-CLINICAL"
    }
