"""
AI Care Navigation Engine, Pharmacology Analyzer & Safety Gateway
Author: Clinical Safety & AI Governance Board

Core Capabilities:
1. Pre-flight Deterministic Red-Flag Safety Gate (Instant 112 / 108 escalation)
2. Conversational Multi-Step Clinical Intake (Step-by-step questions -> Final assessment result)
3. Direct In-Chat Appointment Booking with Verified Specialists
4. Medical Document & Image Parsing (PDF, DOCX, Images, Text)
5. Pharmacology Analysis:
   - Disease / Condition Detection from patient medicines
   - Mechanism of Action explanation in plain language
   - Equivalent Alternatives that perform the same therapeutic work
   - Draft Structured Prescription formulation for doctor sign-off
6. Laboratory Test Analyzer (HbA1c, Glucose, Blood Pressure, Lipids, Hemoglobin, TSH)
"""

import json
from django.conf import settings
from apps.ai_care.protocols.red_flags import evaluate_red_flags
from apps.ai_care.models import AIConversation, AIMessage
from apps.ai_care.services.medical_knowledge import detect_medicines, detect_lab_reports
from apps.doctors.models import DoctorProfile, Specialization


SAFETY_DISCLAIMER = "Notice: The AI Care Assistant provides general symptom navigation and pharmacology education. It is not a substitute for clinical medical diagnosis or treatment. Prescriptions must be certified by a licensed doctor."


class SafetyEngine:
    @staticmethod
    def process_message(conversation: AIConversation, user_text: str, file_text: str = "", filename: str = "") -> dict:
        """
        Main entry point for evaluating patient input and attachments.
        """
        combined_text = f"{user_text}\n{file_text}".strip()

        # Step 1: Pre-flight deterministic clinical red-flag screening
        red_flag_check = evaluate_red_flags(combined_text)

        if red_flag_check["is_red_flag"]:
            conversation.status = AIConversation.STATUS_ESCALATED
            conversation.is_emergency = True
            conversation.save(update_fields=['status', 'is_emergency', 'updated_at'])

            escalation_message = (
                f"🚨 URGENT MEDICAL ADVISORY: Your symptoms indicate a possible critical emergency "
                f"({red_flag_check['label']}).\n\n"
                f"{red_flag_check['clinical_guidance']}\n\n"
                f"⚠️ WHAT YOU MUST DO IMMEDIATELY:\n"
                f"1. Call Emergency Services: Dial {settings.EMERGENCY_PHONE_NUMBER} or Ambulance ({settings.AMBULANCE_PHONE_NUMBER}) right away.\n"
                f"2. If you are alone, alert a family member, neighbor, or nearby person.\n"
                f"3. Go directly to the nearest hospital Emergency Room.\n"
                f"4. Do not attempt to drive yourself if you are feeling dizzy, short of breath, or in severe pain."
            )

            AIMessage.objects.create(
                conversation=conversation,
                role=AIMessage.ROLE_ASSISTANT,
                content=escalation_message,
                category="emergency_escalation",
                urgency="emergency",
                emergency_action_required=True,
                recommended_next_step="call_emergency_112"
            )

            return {
                "message": escalation_message,
                "category": "emergency_escalation",
                "urgency": "emergency",
                "recommended_next_step": "call_emergency_112",
                "needs_human_review": True,
                "emergency_action_required": True,
                "disclaimer": SAFETY_DISCLAIMER
            }

        # Step 2: Pharmacology & Lab Document Analysis
        # Check if the user attached a report or mentioned specific medications/lab tests
        detected_meds = detect_medicines(combined_text)
        detected_labs = detect_lab_reports(combined_text)

        if detected_meds or detected_labs or filename:
            reply_data = SafetyEngine._analyze_medical_document_and_medicines(
                user_text, detected_meds, detected_labs, filename
            )
            # Save assistant message
            AIMessage.objects.create(
                conversation=conversation,
                role=AIMessage.ROLE_ASSISTANT,
                content=reply_data["message"],
                category=reply_data["category"],
                urgency=reply_data["urgency"],
                emergency_action_required=False,
                recommended_next_step=reply_data["recommended_next_step"]
            )
            return reply_data

        # Step 2b: Medication & Generic Replacement Inquiry Handling
        if SafetyEngine._is_medicine_or_replacement_query(combined_text):
            reply_data = SafetyEngine._handle_unrecognized_medicine_query(user_text)
            AIMessage.objects.create(
                conversation=conversation,
                role=AIMessage.ROLE_ASSISTANT,
                content=reply_data["message"],
                category=reply_data["category"],
                urgency=reply_data["urgency"],
                emergency_action_required=False,
                recommended_next_step=reply_data["recommended_next_step"]
            )
            return reply_data

        # Step 3: Multi-Step Symptom Intake Workflow
        reply_data = SafetyEngine._handle_conversational_intake(conversation, user_text)
        AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.ROLE_ASSISTANT,
            content=reply_data["message"],
            category=reply_data["category"],
            urgency=reply_data["urgency"],
            emergency_action_required=False,
            recommended_next_step=reply_data["recommended_next_step"]
        )
        return reply_data

    @staticmethod
    def _analyze_medical_document_and_medicines(user_text: str, meds: list, labs: list, filename: str) -> dict:
        """
        Analyzes uploaded prescriptions, medical reports, or medicine lists.
        Detects underlying diseases, explains mechanisms, suggests equivalent alternatives,
        and builds a draft prescription summary for clinician review.
        """
        sections = []

        if filename:
            sections.append(f"📄 **Medical File Analyzed:** `{filename}`\n")

        # 1. Disease Detection from Medicines
        draft_rx_items = []
        if meds:
            sections.append("### 💊 Detected Medications & Detected Health Conditions\n")
            for m in meds:
                sections.append(
                    f"• **{m['generic_name']}** ({m['therapeutic_class']})\n"
                    f"  - **Detected Condition/Disease:** {m['primary_disease']}\n"
                    f"  - **How it Works:** {m['mechanism_of_action']}\n"
                    f"  - **Standard Formulation:** {m['formulation']} &bull; Typical Dose: {m['standard_dosage']}"
                )

                # Equivalent alternative medicines that do the same work
                if m.get("equivalent_alternatives"):
                    sections.append("\n  - **🔄 Equivalent Medicines with Same Therapeutic Action:**")
                    for alt in m["equivalent_alternatives"]:
                        sections.append(
                            f"    * **{alt['name']}** ({alt['class']}): {alt['how_it_works']} *({alt['typical_use']})*"
                        )
                sections.append("")

                # Build draft prescription item
                draft_rx_items.append({
                    "medicine_name": m["generic_name"],
                    "formulation": m["formulation"].split()[0],
                    "strength": m["standard_dosage"].split()[0] + (" mg" if "mg" in m["standard_dosage"] else ""),
                    "dose": "1 unit",
                    "frequency": "As clinically directed",
                    "duration": "14 days",
                    "instructions": f"Indicated for {m['primary_disease']}. Consult clinician for exact dose."
                })

        # 2. Lab Report Interpretation
        if labs:
            sections.append("### 🔬 Laboratory Report Findings\n")
            for l in labs:
                status_icon = "⚠️" if "high" in l["clinical_status"].lower() or "elevated" in l["clinical_status"].lower() or "low" in l["clinical_status"].lower() else "✅"
                sections.append(
                    f"{status_icon} **{l['test_name']}:** {l['detected_value']} (Normal: {l['reference_range']})\n"
                    f"  - **Status:** **{l['clinical_status']}**\n"
                    f"  - **Clinical Insight:** {l['interpretation']}\n"
                )

        if not meds and not labs:
            sections.append(
                "We received your document. While no specific prescription molecules or standard lab figures were "
                "automatically detected in the text, you can share this file directly with a doctor during your virtual consultation."
            )

        # 3. Next Step & In-Chat Booking Recommendation
        doctor = DoctorProfile.objects.filter(is_verified=True).select_related('user', 'specialization').first()
        recommended_doc = None
        if doctor:
            recommended_doc = {
                "id": str(doctor.id),
                "name": f"Dr. {doctor.user.full_name}",
                "specialization": doctor.specialization.name if doctor.specialization else "General Physician",
                "consultation_fee": str(doctor.consultation_fee),
                "rating": str(doctor.rating),
                "qualifications": doctor.qualifications,
                "city": doctor.city
            }

        sections.append(
            "\n💡 **Clinical Recommendation:**\n"
            "Would you like to schedule a virtual review with a verified doctor to review these medications, "
            "evaluate alternative therapies, and issue an official digital prescription?"
        )

        full_message = "\n".join(sections)

        return {
            "message": full_message,
            "category": "clinician_review",
            "urgency": "routine",
            "recommended_next_step": "book_doctor_appointment",
            "needs_human_review": True,
            "emergency_action_required": False,
            "detected_medicines": meds,
            "detected_lab_findings": labs,
            "draft_prescription": draft_rx_items,
            "can_book_in_chat": True,
            "recommended_doctor": recommended_doc,
            "disclaimer": SAFETY_DISCLAIMER
        }

    @staticmethod
    def _is_medicine_or_replacement_query(text: str) -> bool:
        t = text.lower()
        pharma_words = ["generic", "replacement", "substitute", "alternative", "replace"]
        med_words = ["taking", "medicine", "tablet", "syrup", "capsule", "dosage", "side effect", "drug", "prescription"]
        return any(w in t for w in pharma_words) or (
            any(w in t for w in ["taking", "prescribed", "dose"]) and any(w in t for w in med_words)
        )

    @staticmethod
    def _handle_unrecognized_medicine_query(user_text: str) -> dict:
        import re
        doctor = DoctorProfile.objects.filter(is_verified=True).select_related('user', 'specialization').first()
        recommended_doc = None
        if doctor:
            recommended_doc = {
                "id": str(doctor.id),
                "name": f"Dr. {doctor.user.full_name}",
                "specialization": doctor.specialization.name if doctor.specialization else "General Physician",
                "consultation_fee": str(doctor.consultation_fee),
                "rating": str(doctor.rating),
                "qualifications": doctor.qualifications,
                "city": doctor.city
            }

        match = re.search(r'(?:taking|for|of|replace|substitute|alternative to)\s+([a-zA-Z0-9\s\-]+?)(?:\.|\?|\bis\b|\bfor\b|$)', user_text, re.IGNORECASE)
        med_name = match.group(1).strip() if match else "your queried medication"

        message = (
            f"### 💊 Medication & Generic Replacement Guidance\n\n"
            f"Regarding **{med_name}** and generic alternatives:\n\n"
            f"1. **Understanding Generic Substitutes:**\n"
            f"   - A generic medicine contains the **identical active chemical molecule (API)**, strength, and therapeutic efficacy as the branded version, but typically costs **50% to 80% less**.\n"
            f"   - Check the **generic salt name** printed in smaller font right under the brand name on the strip or bottle.\n\n"
            f"2. **Herbal vs. Allopathic Formulations:**\n"
            f"   - If your medication is an **Ayurvedic/Herbal formulation** (such as herbal cough syrups or immunity tonics), look for equivalent classical herbal formulations containing similar botanical extracts (like Vasa, Tulsi, Mulethi, or Honey).\n"
            f"   - If you need a targeted **allopathic pharmaceutical alternative** (e.g. for wet productive cough vs. dry allergic cough), an exact molecular substitute (like Ambroxol, Levosalbutamol, or Dextromethorphan) may be recommended based on your specific clinical presentation.\n\n"
            f"3. **Clinical Recommendation:**\n"
            f"   - Before switching medications, consult a certified doctor to confirm the exact active molecule, dosage, and ensure there are no adverse drug interactions.\n\n"
            f"Would you like to book a quick video review with a verified clinician to review this medicine and get an authorized prescription?"
        )

        return {
            "message": message,
            "category": "pharmacology_consultation",
            "urgency": "routine",
            "recommended_next_step": "book_doctor_appointment",
            "needs_human_review": True,
            "emergency_action_required": False,
            "can_book_in_chat": True,
            "recommended_doctor": recommended_doc,
            "disclaimer": SAFETY_DISCLAIMER
        }

    @staticmethod
    def _handle_conversational_intake(conversation: AIConversation, user_text: str) -> dict:
        """
        Conducts a structured 4-5 step clinical symptom interview.
        Once all questions are answered, delivers a comprehensive result and
        surfaces an interactive in-chat booking card with a verified specialist!
        """
        user_msg_count = conversation.messages.filter(role=AIMessage.ROLE_USER).count()

        # Step 1 -> Ask about duration & onset
        if user_msg_count == 1:
            reply = (
                f"Thank you for describing your symptoms. To help evaluate this thoroughly:\n\n"
                f"1. **Onset & Duration:** Approximately when did this start? Did it come on suddenly or gradually worsen over the past few days?"
            )
            return {
                "message": reply,
                "category": "routine_care_navigation",
                "urgency": "routine",
                "recommended_next_step": "gather_duration",
                "needs_human_review": False,
                "emergency_action_required": False,
                "can_book_in_chat": False,
                "disclaimer": SAFETY_DISCLAIMER
            }

        # Step 2 -> Ask about severity and progression
        elif user_msg_count == 2:
            reply = (
                f"Thank you for that context.\n\n"
                f"2. **Severity (1-10 Scale):** On a scale from 1 (mild) to 10 (severe), how intense is the discomfort or pain right now?\n"
                f"Is it constant throughout the day, or does it come and go?"
            )
            return {
                "message": reply,
                "category": "routine_care_navigation",
                "urgency": "routine",
                "recommended_next_step": "gather_severity",
                "needs_human_review": False,
                "emergency_action_required": False,
                "can_book_in_chat": False,
                "disclaimer": SAFETY_DISCLAIMER
            }

        # Step 3 -> Ask about associated symptoms & medical history
        elif user_msg_count == 3:
            reply = (
                f"Got it. Two final clinical details:\n\n"
                f"3. **Associated Symptoms & History:** Are you running a fever, feeling dizzy, or having any other symptoms?\n"
                f"Do you have any existing chronic conditions (e.g. hypertension, diabetes) or known drug allergies?"
            )
            return {
                "message": reply,
                "category": "routine_care_navigation",
                "urgency": "routine",
                "recommended_next_step": "gather_history",
                "needs_human_review": False,
                "emergency_action_required": False,
                "can_book_in_chat": False,
                "disclaimer": SAFETY_DISCLAIMER
            }

        # Step 4+ -> Synthesize Complete Intake Assessment Result & Provide In-Chat Booking!
        else:
            all_user_texts = " ".join(
                conversation.messages.filter(role=AIMessage.ROLE_USER).values_list('content', flat=True)
            ).lower()

            # Deduce specialist
            spec_slug = "general-medicine"
            specialty_name = "General Physician"

            if any(k in all_user_texts for k in ["heart", "palpitation", "high bp", "blood pressure", "cholesterol", "pulse"]):
                spec_slug = "cardiology"
                specialty_name = "Cardiologist"
            elif any(k in all_user_texts for k in ["skin", "rash", "itching", "acne", "hair", "eczema"]):
                spec_slug = "dermatology"
                specialty_name = "Dermatologist"
            elif any(k in all_user_texts for k in ["child", "baby", "infant", "pediatric"]):
                spec_slug = "pediatrics"
                specialty_name = "Pediatrician"
            elif any(k in all_user_texts for k in ["joint", "knee", "bone", "back pain", "spine", "ortho"]):
                spec_slug = "orthopedics"
                specialty_name = "Orthopedic Specialist"
            elif any(k in all_user_texts for k in ["anxiety", "depression", "panic", "sleep", "stress"]):
                spec_slug = "psychiatry"
                specialty_name = "Psychiatrist & Wellness Specialist"

            # Query matching verified doctor from database
            matched_doctor = DoctorProfile.objects.filter(
                is_verified=True,
                specialization__slug=spec_slug
            ).select_related('user', 'specialization').first()

            if not matched_doctor:
                matched_doctor = DoctorProfile.objects.filter(is_verified=True).select_related('user', 'specialization').first()

            doc_info = None
            if matched_doctor:
                doc_info = {
                    "id": str(matched_doctor.id),
                    "name": f"Dr. {matched_doctor.user.full_name}",
                    "specialization": matched_doctor.specialization.name if matched_doctor.specialization else specialty_name,
                    "consultation_fee": str(matched_doctor.consultation_fee),
                    "rating": str(matched_doctor.rating),
                    "qualifications": matched_doctor.qualifications,
                    "city": matched_doctor.city
                }

            summary_message = (
                f"### 📋 Clinical Triage Assessment Complete\n\n"
                f"Thank you for completing the symptom evaluation. Here is your structured summary:\n\n"
                f"• **Recommended Department:** **{specialty_name}**\n"
                f"• **Assessed Urgency:** Routine Outpatient Consultation\n"
                f"• **Primary Assessment:** Your reported symptoms have been consolidated into an intake record ready for clinician review.\n\n"
                f"**Self-Care & Comfort Advice while waiting:**\n"
                f"- Ensure adequate hydration with warm fluids.\n"
                f"- Rest comfortably and avoid heavy physical exertion.\n"
                f"- Monitor your symptoms; if fever rises above 101°F or breathing becomes difficult, seek immediate care.\n\n"
                f"👇 **You can book your virtual consultation right here with our verified specialist:**"
            )

            return {
                "message": summary_message,
                "category": "routine_care_navigation",
                "urgency": "routine",
                "recommended_next_step": f"book_{spec_slug}",
                "needs_human_review": True,
                "emergency_action_required": False,
                "can_book_in_chat": True,
                "recommended_doctor": doc_info,
                "disclaimer": SAFETY_DISCLAIMER
            }
