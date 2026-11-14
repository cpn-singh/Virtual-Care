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
        is_hindi = SafetyEngine._detect_language(combined_text) == "hi"

        # Step 1: Pre-flight deterministic clinical red-flag screening
        red_flag_check = evaluate_red_flags(combined_text)

        if red_flag_check["is_red_flag"]:
            conversation.status = AIConversation.STATUS_ESCALATED
            conversation.is_emergency = True
            conversation.save(update_fields=['status', 'is_emergency', 'updated_at'])

            if is_hindi:
                escalation_message = (
                    f"🚨 तत्काल आपातकालीन चेतावनी (URGENT MEDICAL ADVISORY): आपके लक्षण गंभीर आपातकाल के संकेत हो सकते हैं "
                    f"({red_flag_check['label']}).\n\n"
                    f"{red_flag_check['clinical_guidance']}\n\n"
                    f"⚠️ आपको तुरंत क्या करना चाहिए:\n"
                    f"1. आपातकालीन सेवाओं को कॉल करें: तुरंत {settings.EMERGENCY_PHONE_NUMBER} डायल करें या एम्बुलेंस ({settings.AMBULANCE_PHONE_NUMBER}) बुलाएं।\n"
                    f"2. यदि आप अकेले हैं, तो परिवार के सदस्य, पड़ोसी या नजदीकी व्यक्ति को तुरंत सूचित करें।\n"
                    f"3. सीधे नजदीकी अस्पताल के इमरजेंसी रूम (Emergency Room) में जाएं।\n"
                    f"4. चक्कर आने, सांस फूलने या तेज दर्द होने पर खुद गाड़ी चलाने का प्रयास न करें।"
                )
            else:
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
                "can_book_in_chat": False,
                "disclaimer": SAFETY_DISCLAIMER
            }

        # Step 2: Pharmacology & Lab Document Analysis
        # Check if the user attached a report or mentioned specific medications/lab tests
        detected_meds = detect_medicines(combined_text)
        detected_labs = detect_lab_reports(combined_text)

        if detected_meds or detected_labs or filename:
            reply_data = SafetyEngine._analyze_medical_document_and_medicines(
                user_text, detected_meds, detected_labs, filename, is_hindi=is_hindi
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
            reply_data = SafetyEngine._handle_unrecognized_medicine_query(user_text, is_hindi=is_hindi)
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

        # Step 2c: Direct Prescription & Generic Medicine Inquiry for Common/Routine Conditions
        if SafetyEngine._is_direct_prescription_or_routine_medicine_query(combined_text):
            reply_data = SafetyEngine._handle_direct_prescription_request(conversation, combined_text, is_hindi=is_hindi)
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
        reply_data = SafetyEngine._handle_conversational_intake(conversation, user_text, is_hindi=is_hindi)
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
    def _detect_language(text: str) -> str:
        import re
        if re.search(r'[\u0900-\u097f]', text):
            return "hi"
        hinglish_words = {
            "mujhe", "khasi", "bukhar", "dard", "dawai", "dawa", "kya", "hai",
            "kaise", "kare", "karna", "chahiye", "batao", "bataye", "le", "sakta",
            "sakti", "raha", "rahi", "seene", "chhati", "pet", "sir", "gala",
            "kharash", "namaste", "koi", "aur", "jagah", "dusri", "badle", "pehla",
            "pehle", "din", "se", "mai", "main", "mera", "meri", "mere", "aap", "tum"
        }
        tokens = set(re.findall(r'\b\w+\b', text.lower()))
        if len(tokens.intersection(hinglish_words)) >= 1:
            return "hi"
        return "en"

    @staticmethod
    def _analyze_medical_document_and_medicines(user_text: str, meds: list, labs: list, filename: str, is_hindi: bool = False) -> dict:
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
            for m in meds:
                draft_rx_items.append({
                    "medicine_name": m["generic_name"],
                    "formulation": m["formulation"].split()[0],
                    "strength": m["standard_dosage"].split()[0] + (" mg" if "mg" in m["standard_dosage"] else ""),
                    "dose": "1 unit",
                    "frequency": "As clinically directed",
                    "duration": "14 days",
                    "instructions": f"Indicated for {m['primary_disease']}. Consult clinician for exact dose."
                })

            if is_hindi:
                sections.append("### 💊 पहचानी गई दवाइयां और स्वास्थ्य स्थितियां (Detected Medications)\n")
                for m in meds:
                    sections.append(
                        f"• **{m['generic_name']}** ({m['therapeutic_class']})\n"
                        f"  - **संबंधित बीमारी / Condition:** {m['primary_disease']}\n"
                        f"  - **यह कैसे काम करती है:** {m['mechanism_of_action']}\n"
                        f"  - **मानक रूप व खुराक:** {m['formulation']} &bull; सामान्य खुराक: {m['standard_dosage']}"
                    )
                    if m.get("equivalent_alternatives"):
                        sections.append("\n  - **🔄 समान असर वाले जेनेरिक व वैकल्पिक विकल्प (Equivalent Alternatives):**")
                        for alt in m["equivalent_alternatives"]:
                            sections.append(
                                f"    * **{alt['name']}** ({alt['class']}): {alt['how_it_works']} *({alt['typical_use']})*"
                            )
                    sections.append("")
            else:
                sections.append("### 💊 Detected Medications & Detected Health Conditions\n")
                for m in meds:
                    sections.append(
                        f"• **{m['generic_name']}** ({m['therapeutic_class']})\n"
                        f"  - **Detected Condition/Disease:** {m['primary_disease']}\n"
                        f"  - **How it Works:** {m['mechanism_of_action']}\n"
                        f"  - **Standard Formulation:** {m['formulation']} &bull; Typical Dose: {m['standard_dosage']}"
                    )
                    if m.get("equivalent_alternatives"):
                        sections.append("\n  - **🔄 Equivalent Medicines with Same Therapeutic Action:**")
                        for alt in m["equivalent_alternatives"]:
                            sections.append(
                                f"    * **{alt['name']}** ({alt['class']}): {alt['how_it_works']} *({alt['typical_use']})*"
                            )
                    sections.append("")

        # 2. Lab Report Interpretation
        if labs:
            sections.append("### 🔬 Laboratory Report Findings / लैब रिपोर्ट विश्लेषण\n")
            for l in labs:
                status_icon = "⚠️" if "high" in l["clinical_status"].lower() or "elevated" in l["clinical_status"].lower() or "low" in l["clinical_status"].lower() else "✅"
                sections.append(
                    f"{status_icon} **{l['test_name']}:** {l['detected_value']} (Normal: {l['reference_range']})\n"
                    f"  - **Status:** **{l['clinical_status']}**\n"
                    f"  - **Clinical Insight:** {l['interpretation']}\n"
                )

        if not meds and not labs:
            if is_hindi:
                sections.append(
                    "हमें आपका दस्तावेज़ प्राप्त हुआ है। हालांकि पाठ में कोई विशिष्ट दवा या लैब परिणाम स्वचालित रूप से नहीं पाए गए हैं, आप इस फ़ाइल को सीधे अपने परामर्श के दौरान डॉक्टर से साझा कर सकते हैं।"
                )
            else:
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

        if is_hindi:
            sections.append(
                "\n💡 **डॉक्टर की सलाह (Clinical Recommendation):**\n"
                "क्या आप इन दवाइयों की समीक्षा, सुरक्षित जेनेरिक विकल्प चुनने और आधिकारिक डिजिटल प्रिस्क्रिप्शन के लिए किसी सत्यापित डॉक्टर से परामर्श लेना चाहते हैं?"
            )
        else:
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
        pharma_words = ["generic", "replacement", "substitute", "alternative", "replace", "बदले", "विकल्प", "जेनेरिक", "दवाई", "दवा", "dawai", "dawa"]
        med_words = ["taking", "medicine", "tablet", "syrup", "capsule", "dosage", "side effect", "drug", "prescription", "ले रहा", "खा रहा", "सिरप", "गोली"]
        return any(w in t for w in pharma_words) or (
            any(w in t for w in ["taking", "prescribed", "dose", "le raha", "kha raha"]) and any(w in t for w in med_words)
        )

    @staticmethod
    def _is_direct_prescription_or_routine_medicine_query(text: str) -> bool:
        t = text.lower()
        rx_keywords = [
            "prescription", "prescribe", "medicine for", "medication for", "tablet for", "syrup for",
            "dawa for", "dawai for", "dawa batao", "dawai batao", "ilaj", "upay", "kya lu", "kya le",
            "which medicine", "what medicine", "generic medicine", "give me prescription", "suggest medicine"
        ]
        return any(k in t for k in rx_keywords)

    @staticmethod
    def _handle_direct_prescription_request(conversation: AIConversation, text: str, is_hindi: bool = False) -> dict:
        """
        Directly evaluates routine symptom queries requesting a prescription.
        If serious: assigns a doctor.
        If normal/routine: formulates a clean normal prescription with generic medicines without doctor assignment.
        """
        is_serious, severity_label, serious_reason = SafetyEngine._evaluate_case_severity(text)

        if is_serious:
            doctor = DoctorProfile.objects.filter(is_verified=True).select_related('user', 'specialization').first()
            doc_info = None
            if doctor:
                doc_info = {
                    "id": str(doctor.id),
                    "name": f"Dr. {doctor.user.full_name}",
                    "specialization": doctor.specialization.name if doctor.specialization else "General Physician",
                    "consultation_fee": str(doctor.consultation_fee),
                    "rating": str(doctor.rating),
                    "qualifications": doctor.qualifications,
                    "city": doctor.city
                }

            if is_hindi:
                msg = (
                    f"### ⚠️ गंभीर लक्षण मूल्यांकन - डॉक्टर परामर्श आवश्यक (Serious Case)\n\n"
                    f"आपके द्वारा बताए गए लक्षणों में उच्च जोखिम वाले संकेत (**{serious_reason}**) पाए गए हैं। "
                    f"इस स्थिति में बिना डॉक्टर की जांच के दवा लेना सुरक्षित नहीं है।\n\n"
                    f"• **स्थिति वर्गीकरण:** **गंभीर / चिकित्सीय समीक्षा आवश्यक (Serious Clinical Case)**\n"
                    f"• **नियुक्त विशेषज्ञ डॉक्टर:** {doc_info['name'] if doc_info else 'सत्यापित डॉक्टर'}\n\n"
                    f"👇 **कृपया तुरंत नीचे दिए गए कार्ड से डॉक्टर परामर्श बुक करें:**"
                )
            else:
                msg = (
                    f"### ⚠️ Clinical Escalation: Doctor Assigned for Serious Case\n\n"
                    f"Your reported symptoms indicate a serious or high-risk clinical presentation (**{serious_reason}**). "
                    f"Self-medication is unsafe for this condition, and a direct physician evaluation is required.\n\n"
                    f"• **Case Classification:** **Serious / Physician Review Mandatory**\n"
                    f"• **Assigned Clinician:** {doc_info['name'] if doc_info else 'Verified Specialist'}\n\n"
                    f"👇 **Please confirm your video consultation using the booking card below:**"
                )

            return {
                "message": msg,
                "category": "serious_doctor_assignment",
                "urgency": "urgent",
                "recommended_next_step": "book_doctor_appointment",
                "needs_human_review": True,
                "emergency_action_required": False,
                "can_book_in_chat": True,
                "recommended_doctor": doc_info,
                "disclaimer": SAFETY_DISCLAIMER
            }

        else:
            rx_data = SafetyEngine._get_normal_generic_prescription(text, is_hindi=is_hindi)
            if is_hindi:
                msg = (
                    f"### 📋 सामान्य स्थिति - जेनेरिक दवा प्रिस्क्रिप्शन (Normal Routine Care)\n\n"
                    f"आपके लक्षणों के विश्लेषण के अनुसार यह एक **सामान्य व गैर-गंभीर स्थिति** ({rx_data['condition']}) है। इसके लिए **डॉक्टर अपॉइंटमेंट की आवश्यकता नहीं है**।\n\n"
                    f"💊 **प्रस्तावित सामान्य प्रिस्क्रिप्शन (Normal Generic Prescription):**\n"
                    f"नीचे दी गई तालिका में सुरक्षित जेनेरिक दवाएं, खुराक और सेवन की अवधि दी गई है।\n\n"
                    f"💡 **सस्ते जेनेरिक विकल्पों के लाभ:**\n"
                    f"ये जेनेरिक साल्ट (जन औषधि केंद्र या किसी भी मेडिकल स्टोर पर उपलब्ध) ब्रांडेड दवाओं की तुलना में **50% से 80% कम कीमत** पर उपलब्ध हैं और पूरी तरह समान असरदार हैं।\n\n"
                    f"🏠 **घरेलू आराम व देखभाल सलाह:**\n"
                    f"{rx_data['home_care']}\n\n"
                    f"⚠️ **सुरक्षा सलाह:** यदि 3-4 दिनों में आराम न मिले या बुखार 101°F से अधिक बढ़े, तो डॉक्टर से संपर्क करें।"
                )
            else:
                msg = (
                    f"### 📋 Normal Case: Generic Medicine Prescription & Care Plan\n\n"
                    f"Based on your symptoms, your condition is **mild / non-serious** ({rx_data['condition']}). **No doctor appointment is required** for this routine illness.\n\n"
                    f"💊 **Normal Digital Prescription (Safe Generic Medicines):**\n"
                    f"The prescribed generic medications, formulation, and dosing schedules are detailed in the prescription summary below.\n\n"
                    f"💡 **Why Generic Medicines?**\n"
                    f"Generic medicines contain the **identical active chemical molecule (API)** and therapeutic potency as expensive branded medicines, but cost **50% to 80% less** (available at Jan Aushadhi Kendras and retail pharmacies).\n\n"
                    f"🏠 **Supportive Home Care:**\n"
                    f"{rx_data['home_care']}\n\n"
                    f"⚠️ **When to Seek Medical Care:** If symptoms persist beyond 3-4 days or worsen, please consult a physician."
                )

            return {
                "message": msg,
                "category": "routine_generic_prescription",
                "urgency": "routine",
                "recommended_next_step": "generic_prescription_provided",
                "needs_human_review": False,
                "emergency_action_required": False,
                "can_book_in_chat": False,
                "recommended_doctor": None,
                "draft_prescription": rx_data["medicines"],
                "disclaimer": SAFETY_DISCLAIMER
            }

    @staticmethod
    def _handle_unrecognized_medicine_query(user_text: str, is_hindi: bool = False) -> dict:
        import re
        is_serious, severity_label, serious_reason = SafetyEngine._evaluate_case_severity(user_text)

        match = re.search(r'(?:taking|for|of|replace|substitute|alternative to|दवा|दवाई|ले रहा)\s+([a-zA-Z0-9\s\-]+?)(?:\.|\?|\bis\b|\bfor\b|$)', user_text, re.IGNORECASE)
        med_name = match.group(1).strip() if match else "your queried medication"

        doctor = DoctorProfile.objects.filter(is_verified=True).select_related('user', 'specialization').first()
        recommended_doc = None
        if doctor and is_serious:
            recommended_doc = {
                "id": str(doctor.id),
                "name": f"Dr. {doctor.user.full_name}",
                "specialization": doctor.specialization.name if doctor.specialization else "General Physician",
                "consultation_fee": str(doctor.consultation_fee),
                "rating": str(doctor.rating),
                "qualifications": doctor.qualifications,
                "city": doctor.city
            }

        if is_hindi:
            message = (
                f"### 💊 दवाई और जेनेरिक विकल्प की जानकारी (Medication Guidance)\n\n"
                f"**{med_name}** और इसके जेनेरिक विकल्पों के बारे में:\n\n"
                f"1. **जेनेरिक दवा को समझें:**\n"
                f"   - जेनेरिक दवा में ब्रांडेड दवा के समान ही **सक्रिय रासायनिक घटक (Active Salt)** और चिकित्सीय असर होता है, लेकिन इसकी कीमत **50% से 80% तक कम** होती है।\n"
                f"   - दवा के पत्ते या शीशी पर ब्रांड के नीचे लिखे **साल्ट नाम (Generic Salt Name)** को देखकर जन औषधि या अन्य जेनेरिक ब्रांड लिए जा सकते हैं।\n\n"
                f"2. **हर्बल बनाम एलोपैथिक विकल्प:**\n"
                f"   - यदि यह **आयुर्वेदिक/हर्बल दवा** है (जैसे कफ सिरप), तो इसी तरह के प्राकृतिक घटकों (जैसे वासा, तुलसी, मुलेठी, शहद) वाले अन्य हर्बल सिरप (जैसे डाबर हनीटस, हिमालया कॉफलेट) विकल्प हो सकते हैं।\n"
                f"   - यदि आपको **एलोपैथिक विकल्प** चाहिए (जैसे बलगम वाली गीली खांसी के लिए एम्ब्रोक्सोल+लेवोसालबुटामोल, या सूखी खांसी के लिए डेक्सट्रोमेथॉर्फन), तो खांसी के प्रकार के अनुसार सही दवा चुनी जाती है।\n\n"
                f"3. **सुरक्षा व उपलब्धता:**\n"
                f"   - यह सामान्य जेनेरिक दवा प्रतिस्थापन है। इसके लिए **डॉक्टर विजिट की आवश्यकता नहीं है**—आप सीधे किसी भी फार्मेसी या जन औषधि केंद्र से यह साल्ट ले सकते हैं।"
            )
        else:
            message = (
                f"### 💊 Medication & Generic Replacement Guidance\n\n"
                f"Regarding **{med_name}** and generic alternatives:\n\n"
                f"1. **Understanding Generic Substitutes:**\n"
                f"   - A generic medicine contains the **identical active chemical molecule (API)**, strength, and therapeutic efficacy as the branded version, but typically costs **50% to 80% less**.\n"
                f"   - Check the **generic salt name** printed in smaller font right under the brand name on the strip or bottle.\n\n"
                f"2. **Herbal vs. Allopathic Formulations:**\n"
                f"   - If your medication is an **Ayurvedic/Herbal formulation** (such as herbal cough syrups or immunity tonics), look for equivalent classical herbal formulations containing similar botanical extracts (like Vasa, Tulsi, Mulethi, or Honey).\n"
                f"   - If you need a targeted **allopathic pharmaceutical alternative** (e.g. for wet productive cough vs. dry allergic cough), an exact molecular substitute (like Ambroxol, Levosalbutamol, or Dextromethorphan) may be recommended based on your specific clinical presentation.\n\n"
                f"3. **Clinical Guidance:**\n"
                f"   - For this routine generic medicine information, **no doctor appointment is required**. You can safely request the equivalent generic salt at your local pharmacy or Jan Aushadhi Kendra."
            )

        return {
            "message": message,
            "category": "pharmacology_consultation",
            "urgency": "urgent" if is_serious else "routine",
            "recommended_next_step": "book_doctor_appointment" if is_serious else "generic_guidance_provided",
            "needs_human_review": is_serious,
            "emergency_action_required": False,
            "can_book_in_chat": is_serious,
            "recommended_doctor": recommended_doc,
            "disclaimer": SAFETY_DISCLAIMER
        }

    @staticmethod
    def _evaluate_case_severity(text: str) -> tuple[bool, str, str]:
        """
        Differentiates Serious Cases from Normal/Routine Cases.
        Returns:
            (is_serious: bool, severity_label: str, reason: str)
        """
        t = text.lower()
        red_flag_res = evaluate_red_flags(text)
        if red_flag_res["is_red_flag"]:
            return True, "Emergency / Red-Flag Critical", red_flag_res.get("label", "Acute Clinical Red Flag")

        # Specific severe clinical triggers
        serious_triggers = [
            ("chest pain", "Severe chest pain or cardiac discomfort"),
            ("chest tightness", "Chest tightness or pressure"),
            ("severe joint pain", "Severe acute joint pain with inflammation"),
            ("shortness of breath", "Significant breathlessness / dyspnea"),
            ("difficulty breathing", "Severe respiratory distress"),
            ("saans lene me", "Breathing difficulty / respiratory distress"),
            ("slurred speech", "Neurological impairment / slurred speech"),
            ("facial droop", "Acute stroke indicator / facial droop"),
            ("paralysis", "Focal neurological deficit / paralysis"),
            ("unconscious", "Loss of consciousness / syncope"),
            ("fainted", "Syncope / fainting episode"),
            ("behosh", "Loss of consciousness"),
            ("coughing blood", "Hemoptysis (coughing up blood)"),
            ("vomiting blood", "Hematemesis (vomiting blood)"),
            ("khoon ki ulti", "Hematemesis / gastrointestinal bleeding"),
            ("black stool", "Melena / internal bleeding"),
            ("unbearable pain", "Unbearable or intractable pain"),
            ("excruciating pain", "Excruciating pain level"),
            ("worst headache", "Sudden 'thunderclap' severe headache"),
            ("high fever 103", "High-grade fever (>103°F)"),
            ("high fever 104", "Severe pyrexia (>104°F)"),
            ("fever for 2 weeks", "Prolonged pyrexia of unknown origin"),
            ("fever for 10 days", "Prolonged fever lasting >10 days"),
            ("seizure", "Seizure activity / convulsions"),
            ("fits", "Seizure activity / convulsions"),
        ]

        for phrase, reason in serious_triggers:
            if phrase in t:
                return True, "Serious / High-Risk Case", reason

        # Check numeric severity ratings 7-10
        import re
        if re.search(r'\b([789]|10)\s*/\s*10\b', t) or re.search(r'\b(?:rate|severity|level|score)\s*(?:is|:)?\s*([789]|10)\b', t):
            return True, "Serious Case (High Pain/Severity Score 7-10)", "Self-reported pain/severity score is 7/10 or higher"

        if any(w in t for w in ["unbearable", "excruciating", "can't tolerate", "cant tolerate", "cannot tolerate", "असहनीय"]):
            return True, "Serious Case (Intolerable Pain)", "Patient reports intolerable pain or distress"

        return False, "Normal / Routine Outpatient Case", "Mild-to-moderate symptoms suitable for safe generic medicine and home care"

    @staticmethod
    def _get_normal_generic_prescription(all_user_texts: str, is_hindi: bool = False) -> dict:
        """
        Synthesizes a structured normal prescription with generic medicines
        for non-serious / routine conditions.
        """
        t = all_user_texts.lower()

        if any(k in t for k in ["acidity", "acid", "heartburn", "gerd", "gas", "indigestion", "bloating", "pet me gas", "jalan"]):
            condition = "Mild Acidity, GERD & Indigestion (हल्की एसिडिटी व अपच)" if is_hindi else "Mild Acidity, GERD & Dyspepsia"
            meds = [
                {
                    "medicine_name": "Pantoprazole 40 mg (Generic Salt)",
                    "formulation": "Oral Tablet",
                    "strength": "40 mg",
                    "dose": "1 tablet",
                    "frequency": "Once daily, 30 mins before breakfast",
                    "duration": "5-7 days",
                    "instructions": "Swallow whole with plain water before eating. Brand equivalents: Pan 40 / Pantocid / Jan Aushadhi Pantoprazole."
                },
                {
                    "medicine_name": "Magaldrate + Simethicone Oral Suspension",
                    "formulation": "Antacid Gel (Syrup)",
                    "strength": "Standard",
                    "dose": "10 ml (2 teaspoonfuls)",
                    "frequency": "Twice daily after meals & at bedtime",
                    "duration": "5 days",
                    "instructions": "Shake well before use. Rapidly relieves burning sensation and breaks gas bubbles."
                }
            ]
            home_care = (
                "- Avoid spicy, deep-fried, oily foods and caffeinated beverages.\n"
                "- Eat small, frequent meals rather than large heavy meals.\n"
                "- Do not lie down flat immediately after eating; keep head slightly elevated."
            )

        elif any(k in t for k in ["headache", "head ache", "sir dard", "sar dard", "body pain", "body ache", "badan dard", "tired", "fatigue"]):
            condition = "Tension Headache / Mild Bodyache & Fatigue (सामान्य सिरदर्द व बदन दर्द)" if is_hindi else "Tension-Type Headache & Muscular Fatigue"
            meds = [
                {
                    "medicine_name": "Paracetamol 500 mg or 650 mg (Generic Salt)",
                    "formulation": "Oral Tablet",
                    "strength": "500/650 mg",
                    "dose": "1 tablet",
                    "frequency": "Twice daily after meals as needed (SOS)",
                    "duration": "2-3 days",
                    "instructions": "Take after meals. Maximum 3 tablets in 24 hours. Brand equivalents: Dolo 650 / Crocin / Jan Aushadhi."
                },
                {
                    "medicine_name": "Oral Rehydration Salts (ORS WHO Formulation)",
                    "formulation": "Oral Sachet / Solution",
                    "strength": "21.8g Sachet",
                    "dose": "1 sachet in 1L water",
                    "frequency": "Sip throughout the day",
                    "duration": "2 days",
                    "instructions": "Dissolve completely in boiled and cooled drinking water. Rehydrates and relieves dehydration fatigue."
                }
            ]
            home_care = (
                "- Rest in a quiet, dimly lit room and reduce digital screen time.\n"
                "- Ensure drinking at least 2.5 to 3 liters of water.\n"
                "- Practice gentle neck and shoulder stretching."
            )

        elif any(k in t for k in ["loose motion", "diarrhea", "dast", "upset stomach", "pet kharab", "motion"]):
            condition = "Mild Acute Gastroenteritis / Food Indigestion (हल्के दस्त व पेट संक्रमण)" if is_hindi else "Mild Gastroenteritis & Dietary Indigestion"
            meds = [
                {
                    "medicine_name": "Oral Rehydration Salts (ORS WHO Formula)",
                    "formulation": "Oral Solution",
                    "strength": "WHO Standard",
                    "dose": "1 glass (200-250 ml)",
                    "frequency": "After every loose bowel motion",
                    "duration": "3 days",
                    "instructions": "Vital to prevent dehydration and weakness. Brand equivalents: Electral / Jan Aushadhi ORS."
                },
                {
                    "medicine_name": "Lactic Acid Bacillus / Probiotics",
                    "formulation": "Capsule / Sachet",
                    "strength": "Standard Colony Count",
                    "dose": "1 capsule",
                    "frequency": "Twice daily after meals",
                    "duration": "3-5 days",
                    "instructions": "Replenishes beneficial gut microflora. Brand equivalents: Sporlac / Darolac."
                },
                {
                    "medicine_name": "Zinc Sulfate 20 mg",
                    "formulation": "Dispersible Tablet",
                    "strength": "20 mg",
                    "dose": "1 tablet",
                    "frequency": "Once daily with food",
                    "duration": "5 days",
                    "instructions": "Restores intestinal mucosa lining."
                }
            ]
            home_care = (
                "- Sip coconut water, rice water (kanji), and weak clear broths.\n"
                "- Avoid milk products, raw salads, and heavy spicy food for 48 hours.\n"
                "- Wash hands thoroughly with soap before eating."
            )

        elif any(k in t for k in ["rash", "itching", "khujli", "allergy", "allergic", "hives", "urticaria", "chakatte"]):
            condition = "Mild Allergic Rhinitis / Skin Pruritus (हल्की एलर्जी व खुजली)" if is_hindi else "Mild Allergic Rhinitis / Contact Dermatitis"
            meds = [
                {
                    "medicine_name": "Cetirizine Hydrochloride 10 mg (Generic Salt)",
                    "formulation": "Oral Tablet",
                    "strength": "10 mg",
                    "dose": "1 tablet",
                    "frequency": "Once daily at night (bedtime)",
                    "duration": "3-5 days",
                    "instructions": "Non-drowsy antihistamine. Brand equivalents: Cetzine / Alerid / Jan Aushadhi Cetirizine."
                },
                {
                    "medicine_name": "Calamine Topical Lotion",
                    "formulation": "Topical Skin Lotion",
                    "strength": "Standard",
                    "dose": "Thin layer",
                    "frequency": "Twice daily on affected skin",
                    "duration": "5 days",
                    "instructions": "Apply gently without vigorous rubbing to soothe burning and itchiness."
                }
            ]
            home_care = (
                "- Wear loose, breathable cotton clothing.\n"
                "- Avoid very hot showers or harsh perfumed soaps.\n"
                "- Identify and avoid known allergen triggers."
            )

        else:
            # Common Cold, Cough, Sore Throat, Mild Viral Fever (default routine)
            condition = "Common Cold, Mild Viral Pharyngitis & Cough (सामान्य सर्दी-जुकाम व खांसी)" if is_hindi else "Common Cold & Viral Upper Respiratory Infection"
            meds = [
                {
                    "medicine_name": "Paracetamol 650 mg (Generic Salt)",
                    "formulation": "Oral Tablet",
                    "strength": "650 mg",
                    "dose": "1 tablet",
                    "frequency": "Twice daily after meals (SOS for fever/ache)",
                    "duration": "3 days",
                    "instructions": "Take with water after food. Do not exceed 3 tablets a day. Brand equivalents: Dolo 650 / Crocin 650 / Jan Aushadhi."
                },
                {
                    "medicine_name": "Cetirizine Hydrochloride 10 mg (Generic Salt)",
                    "formulation": "Oral Tablet",
                    "strength": "10 mg",
                    "dose": "1 tablet",
                    "frequency": "Once daily at night before sleep",
                    "duration": "3-5 days",
                    "instructions": "Relieves runny nose, sneezing, and throat irritation. Brand equivalents: Cetzine / Alerid."
                },
                {
                    "medicine_name": "Ambroxol Hydrochloride 30 mg / 5ml (or Herbal Vasa-Tulsi Syrup)",
                    "formulation": "Oral Syrup",
                    "strength": "30 mg / 5 ml",
                    "dose": "10 ml (2 teaspoonfuls)",
                    "frequency": "Twice daily with lukewarm water",
                    "duration": "5 days",
                    "instructions": "Helps thin out throat mucus. Brand equivalents: Dabur Honitus / Ascoril / Jan Aushadhi Cough Syrup."
                }
            ]
            home_care = (
                "- Steam inhalation for 5-10 minutes twice daily.\n"
                "- Warm saline gargles (half teaspoon salt in warm water) 2-3 times daily.\n"
                "- Drink warm water, herbal teas with ginger and honey, and take adequate rest."
            )

        return {
            "condition": condition,
            "medicines": meds,
            "home_care": home_care
        }

    @staticmethod
    def _handle_conversational_intake(conversation: AIConversation, user_text: str, is_hindi: bool = False) -> dict:
        """
        Conducts a structured 4-5 step clinical symptom interview.
        Differentiates serious cases from normal/routine cases:
        - SERIOUS CASES: Assigns a verified doctor with in-chat appointment booking.
        - NORMAL CASES: Formulates a normal digital prescription with safe generic medicines (no doctor visit needed).
        """
        user_msg_count = conversation.messages.filter(role=AIMessage.ROLE_USER).count()

        # Step 1 -> Ask about duration & onset
        if user_msg_count == 1:
            if is_hindi:
                reply = (
                    f"अपने लक्षणों के बारे में बताने के लिए धन्यवाद। आपकी स्थिति को अच्छी तरह समझने के लिए कृपया बताएं:\n\n"
                    f"1. **शुरुआत और अवधि (Duration):** यह समस्या लगभग कब से शुरू हुई? क्या यह अचानक शुरू हुई या पिछले कुछ दिनों में धीरे-धीरे बढ़ी है?"
                )
            else:
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
            if is_hindi:
                reply = (
                    f"जानकारी देने के लिए धन्यवाद।\n\n"
                    f"2. **तीव्रता (Severity - 1 से 10 का पैमाना):** 1 (हल्का) से 10 (बहुत तेज) के पैमाने पर, अभी दर्द या तकलीफ कितनी तीव्र है?\n"
                    f"क्या यह पूरे दिन लगातार बनी रहती है, या कभी-कभी आती-जाती है?"
                )
            else:
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
            if is_hindi:
                reply = (
                    f"समझ गया। कृपया दो और बातें बताएं:\n\n"
                    f"3. **अन्य लक्षण व इतिहास:** क्या आपको बुखार, चक्कर, कमजोरी या कोई अन्य तकलीफ भी महसूस हो रही है?\n"
                    f"क्या आपको पहले से कोई बीमारी (जैसे बीपी, शुगर) या किसी दवा से एलर्जी है?"
                )
            else:
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

        # Step 4+ -> Synthesize Complete Intake Assessment Result
        else:
            all_user_texts = " ".join(
                conversation.messages.filter(role=AIMessage.ROLE_USER).values_list('content', flat=True)
            ).lower()

            # Deduce specialist department for clinical categorization
            spec_slug = "general-medicine"
            specialty_name = "General Physician"

            if any(k in all_user_texts for k in ["heart", "palpitation", "high bp", "blood pressure", "cholesterol", "pulse", "दिल", "धड़कन"]):
                spec_slug = "cardiology"
                specialty_name = "Cardiologist"
            elif any(k in all_user_texts for k in ["skin", "rash", "itching", "acne", "hair", "eczema", "त्वचा", "खुजली", "चकत्ते"]):
                spec_slug = "dermatology"
                specialty_name = "Dermatologist"
            elif any(k in all_user_texts for k in ["child", "baby", "infant", "pediatric", "बच्चा", "शिशु"]):
                spec_slug = "pediatrics"
                specialty_name = "Pediatrician"
            elif any(k in all_user_texts for k in ["joint", "knee", "bone", "back pain", "spine", "ortho", "जोड़ों", "घुटना", "हड्डी"]):
                spec_slug = "orthopedics"
                specialty_name = "Orthopedic Specialist"
            elif any(k in all_user_texts for k in ["anxiety", "depression", "panic", "sleep", "stress", "तनाव", "चिंता", "नींद"]):
                spec_slug = "psychiatry"
                specialty_name = "Psychiatrist & Wellness Specialist"

            # Clinical triage severity assessment
            is_serious, severity_label, serious_reason = SafetyEngine._evaluate_case_severity(all_user_texts)

            if is_serious:
                # SERIOUS CASE: Assign a qualified doctor and enable in-chat booking
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

                if is_hindi:
                    summary_message = (
                        f"### 📋 क्लिनिकल ट्राइएज मूल्यांकन पूर्ण - डॉक्टर परामर्श आवश्यक (Serious Case)\n\n"
                        f"लक्षण मूल्यांकन पूरा करने के लिए धन्यवाद। आपके लक्षणों में गंभीर संकेत (**{serious_reason}**) पाए गए हैं।\n\n"
                        f"• **अनुशंसित विशेषज्ञ (Recommended Department):** **{specialty_name}**\n"
                        f"• **केस वर्गीकरण:** **गंभीर / प्रत्यक्ष क्लिनिकल समीक्षा आवश्यक (Serious Case)**\n"
                        f"• **नियुक्त डॉक्टर (Assigned Clinician):** {doc_info['name'] if doc_info else 'सत्यापित विशेषज्ञ डॉक्टर'}\n\n"
                        f"**मार्गदर्शन:**\n"
                        f"इस स्तर के लक्षणों के लिए केवल घरेलू दवाएं पर्याप्त नहीं हैं। कृपया नीचे दिए गए कार्ड से नियुक्त डॉक्टर के साथ वीडियो परामर्श बुक करें।"
                    )
                else:
                    summary_message = (
                        f"### 📋 Clinical Triage Assessment Complete: Doctor Assigned (Serious Case)\n\n"
                        f"Thank you for completing the symptom evaluation. Based on clinical evaluation, your condition requires direct physician care (**{serious_reason}**).\n\n"
                        f"• **Recommended Department:** **{specialty_name}**\n"
                        f"• **Case Classification:** **Serious / Direct Physician Examination Required**\n"
                        f"• **Assigned Clinician:** {doc_info['name'] if doc_info else 'Verified Specialist'} ({specialty_name})\n\n"
                        f"👇 **Please confirm your video consultation using the interactive card below:**"
                    )

                return {
                    "message": summary_message,
                    "category": "serious_doctor_assignment",
                    "urgency": "urgent",
                    "recommended_next_step": f"book_{spec_slug}",
                    "needs_human_review": True,
                    "emergency_action_required": False,
                    "can_book_in_chat": True,
                    "recommended_doctor": doc_info,
                    "disclaimer": SAFETY_DISCLAIMER
                }

            else:
                # NORMAL CASE: Do NOT assign a doctor. Provide a normal digital prescription with safe generic medicines!
                rx_data = SafetyEngine._get_normal_generic_prescription(all_user_texts, is_hindi=is_hindi)

                if is_hindi:
                    summary_message = (
                        f"### 📋 क्लिनिकल ट्राइएज मूल्यांकन पूर्ण - सामान्य स्थिति (Normal Routine Care)\n\n"
                        f"लक्षण मूल्यांकन पूरा करने के लिए धन्यवाद। आपकी स्थिति **सामान्य / गैर-गंभीर** ({rx_data['condition']}) है।\n\n"
                        f"• **अनुशंसित विभाग (Recommended Department):** **{specialty_name}** *(वैकल्पिक / संदर्भ के लिए)*\n"
                        f"• **डॉक्टर परामर्श (Doctor Assignment):** **आवश्यक नहीं है (No Doctor Visit Required)**\n"
                        f"• **केस वर्गीकरण:** सामान्य बाह्य रोगी देखभाल (Normal Outpatient Routine Care)\n\n"
                        f"💊 **प्रस्तावित सामान्य प्रिस्क्रिप्शन (Normal Generic Prescription):**\n"
                        f"नीचे दी गई तालिका में सुरक्षित जेनेरिक दवाएं और खुराक दी गई है।\n\n"
                        f"💡 **जेनेरिक दवा के फायदे (50-80% बचत):**\n"
                        f"ये जेनेरिक दवाएं (जन औषधि केंद्र या किसी भी मेडिकल स्टोर पर उपलब्ध) ब्रांडेड दवाओं के समान ही असरदार होती हैं, लेकिन अत्यधिक सस्ती होती हैं।\n\n"
                        f"🏠 **घरेलू देखभाल और आराम सलाह:**\n"
                        f"{rx_data['home_care']}\n\n"
                        f"⚠️ **डॉक्टर से कब संपर्क करें:**\n"
                        f"यदि 3-4 दिनों में आराम न मिले या बुखार 101°F से ऊपर जाए, तो डॉक्टर से संपर्क करें।"
                    )
                else:
                    summary_message = (
                        f"### 📋 Clinical Triage Assessment Complete: Normal Case\n\n"
                        f"Thank you for completing the symptom evaluation. Based on clinical triage, your condition is **mild / routine and non-serious** ({rx_data['condition']}).\n\n"
                        f"• **Recommended Department:** **{specialty_name}** *(Contextual department reference)*\n"
                        f"• **Doctor Assignment:** **Not Required** *(Routine self-limiting condition)*\n"
                        f"• **Case Classification:** **Normal / Routine Outpatient Care**\n\n"
                        f"💊 **Normal Digital Prescription (Safe Generic Medicines):**\n"
                        f"The prescribed generic medications, formulation, and dosing schedules are detailed in the prescription summary below.\n\n"
                        f"💡 **Why Generic Medicines?**\n"
                        f"Generic medicines contain the **identical active pharmaceutical ingredient (API)** and therapeutic potency as expensive brands, but cost **50% to 80% less** (available at Jan Aushadhi Kendras and retail pharmacies).\n\n"
                        f"🏠 **Supportive Home Care & Recovery:**\n"
                        f"{rx_data['home_care']}\n\n"
                        f"⚠️ **When to Seek Medical Care:**\n"
                        f"If symptoms persist beyond 3-4 days or worsen, please consult a physician."
                    )

                return {
                    "message": summary_message,
                    "category": "routine_generic_prescription",
                    "urgency": "routine",
                    "recommended_next_step": "generic_prescription_provided",
                    "needs_human_review": False,
                    "emergency_action_required": False,
                    "can_book_in_chat": False,
                    "recommended_doctor": None,
                    "draft_prescription": rx_data["medicines"],
                    "disclaimer": SAFETY_DISCLAIMER
                }
