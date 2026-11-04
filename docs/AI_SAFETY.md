# AI Care Assistant & Clinical Safety Protocol

**Protocol Version:** `1.0.4-CLINICAL`  
**Governance:** Telehealth Clinical Governance & Safety Board  
**Target Audience:** Clinical Reviewers, Compliance Officers, Platform Engineers

---

## 1. Safety Principles & Core Boundaries

The Virtual Care AI Assistant is strictly a **care navigation, triage, and educational assistant**. It is **not** an autonomous doctor.

1. **Never Diagnoses:** The system does not claim or imply a definitive medical diagnosis.
2. **Never Prescribes:** The system never suggests specific prescription drugs, dosages, or alters ongoing medication plans.
3. **No Emergency Delays:** Deterministic safety checks run *before* any natural language processing or external LLMs.
4. **Always Reachable Clinician:** Every interaction provides clear paths to consult human clinicians or contact physical emergency departments.
5. **Transparency & Disclaimer:** Every message explicitly reminds users that AI output is for guidance only.

---

## 2. Red-Flag Deterministic Screening Engine

Prior to invoking any language model, patient inputs are scanned by the deterministic `evaluate_red_flags()` engine located at:
`backend/apps/ai_care/protocols/red_flags.py`

### Monitored Acute Categories

| Category | Primary Symptom Triggers | Action Taken |
| :--- | :--- | :--- |
| **Cardiac** | Crushing chest pain, left arm/jaw radiation, heart tightness | Immediate Emergency Escalation (112 / 108) |
| **Respiratory** | Inability to breathe, suffocating, gasping, cyanosis, choking | Immediate Emergency Escalation (112 / 108) |
| **Stroke (FAST)** | Facial drooping, unilateral arm weakness, slurred speech | Immediate Emergency Escalation (112 / 108) |
| **Hemorrhage** | Heavy bleeding, coughing/vomiting blood, trauma | Immediate Emergency Escalation (112 / 108) |
| **Anaphylaxis** | Throat closing, lip/tongue swelling, severe allergy | Immediate Emergency Escalation (112 / 108) |
| **Poisoning/Overdose** | Drug overdose, chemical ingestion, pesticides | Immediate Emergency Escalation (112 / 108) |
| **Mental Crisis** | Acute suicidal ideation, self-harm intentions | Crisis Helpline & Emergency Escalation |

---

## 3. Standard Response Schema Contract

All triage outputs conform strictly to the following JSON schema:

```json
{
  "message": "Plain-language, empathetic guidance for the patient",
  "category": "routine_care_navigation",
  "urgency": "routine",
  "recommended_next_step": "book_general_physician",
  "needs_human_review": true,
  "emergency_action_required": false,
  "disclaimer": "AI guidance is not a medical diagnosis. In an emergency, dial 112."
}
```

Allowed categories:
- `platform_support`
- `general_information`
- `routine_care_navigation`
- `clinician_review`
- `emergency_escalation`

---

## 4. Clinician Handoff Packaging

When patients transition from the AI Care Assistant to a doctor's consultation, the system summarizes patient-reported symptoms into structured intake notes (`AIHandoff`). The attending physician reviews this summary as preliminary context during the consultation.
