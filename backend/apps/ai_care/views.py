"""
AI Care API Views
Author: Clinical Safety & AI Governance Team

Handles:
- Creating anonymous or authenticated symptom intake sessions
- Sending messages & file attachments (PDF, DOCX, Images, TXT)
- Multi-question symptom intake with automatic appointment matching
- Pharmacology disease detection, equivalent alternatives & draft prescriptions
- Summarizing patient symptom handoffs for doctor consultations
"""

import secrets
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.ai_care.models import AIConversation, AIMessage, AIHandoff
from apps.ai_care.serializers import (
    AIConversationSerializer,
    SendMessageInputSerializer,
    AIHandoffSerializer,
)
from apps.ai_care.services.safety_engine import SafetyEngine
from apps.ai_care.services.document_parser import DocumentParser
from apps.patients.models import PatientProfile
from common.responses import success_response, error_response


class AICareSessionCreateView(APIView):
    """
    POST /api/v1/ai-care/sessions/
    Initializes a new care assistant session.
    Open to everyone (no login required for emergency access).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        session_token = secrets.token_hex(24)

        conversation = AIConversation.objects.create(
            user=user,
            session_token=session_token,
            title="General Symptom Navigation"
        )

        # Welcome message from AI Care Assistant
        welcome_text = (
            "Hello! I am your Virtual Care Assistant. I am here to help you evaluate your symptoms, "
            "read your medical reports or prescription lists, and connect you with the right specialist.\n\n"
            "📎 You can attach medical documents (Images, PDFs, Word docs) or type your symptoms below.\n\n"
            "⚠️ Please note: I am an AI assistant and cannot provide definitive medical diagnoses or issue legal prescriptions. "
            "In an acute emergency, dial 112 immediately.\n\n"
            "What symptoms are you experiencing today?"
        )

        AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.ROLE_ASSISTANT,
            content=welcome_text,
            category="general_information",
            urgency="routine",
            recommended_next_step="gather_symptoms"
        )

        return success_response(
            data=AIConversationSerializer(conversation).data,
            message="Care session initialized.",
            http_status=status.HTTP_201_CREATED
        )


class AICareSendMessageView(APIView):
    """
    POST /api/v1/ai-care/sessions/<id>/messages/
    Accepts text messages and/or uploaded medical files (PDF, DOC, Images).
    Performs deterministic red-flag screening, pharmacology disease detection,
    and structured in-chat doctor booking matching.
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, session_id):
        conversation = AIConversation.objects.filter(id=session_id).first()
        if not conversation:
            return error_response(message="Care session not found.", http_status=status.HTTP_404_NOT_FOUND)

        user_text = request.data.get('message', '').strip()
        uploaded_file = request.FILES.get('file')

        file_text = ""
        filename = ""

        if uploaded_file:
            filename = uploaded_file.name
            file_text = DocumentParser.extract_text_from_file(uploaded_file, filename)

        if not user_text and not file_text:
            return error_response(message="Please provide a message or attach a valid medical document.")

        # Display user message in chat
        display_content = user_text
        if filename:
            display_content = f"{user_text}\n[Attached File: {filename}]".strip()

        AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.ROLE_USER,
            content=display_content
        )

        # Process through clinical safety & pharmacology engine
        reply_data = SafetyEngine.process_message(
            conversation=conversation,
            user_text=user_text,
            file_text=file_text,
            filename=filename
        )

        return success_response(
            data={
                "session_id": conversation.id,
                "status": conversation.status,
                "is_emergency": conversation.is_emergency,
                "response": reply_data,
            },
            message="Response generated."
        )


class AICareHandoffView(APIView):
    """
    POST /api/v1/ai-care/sessions/<id>/handoff/
    Compiles the conversation into a clinical summary that can be attached
    to an appointment for the doctor's review.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, session_id):
        conversation = AIConversation.objects.filter(id=session_id).first()
        if not conversation:
            return error_response(message="Care session not found.", http_status=status.HTTP_404_NOT_FOUND)

        user_messages = conversation.messages.filter(role=AIMessage.ROLE_USER).values_list('content', flat=True)
        symptoms_text = "; ".join(user_messages) if user_messages else "Patient requested doctor consultation."

        patient_profile = None
        if request.user.is_authenticated:
            patient_profile = PatientProfile.objects.filter(user=request.user).first()

        handoff, _ = AIHandoff.objects.get_or_create(
            conversation=conversation,
            defaults={
                'patient': patient_profile,
                'symptom_summary': f"Patient-reported intake: {symptoms_text[:1000]}",
                'recommended_specialization': "General Physician"
            }
        )

        return success_response(
            data=AIHandoffSerializer(handoff).data,
            message="Intake summary generated for doctor consultation."
        )
