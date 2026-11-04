"""
Consultation API Views
Author: Telehealth Video & Media Team

Handles active video encounters, clinical note authoring by verified doctors,
and call completion states.
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from django.utils import timezone
from apps.consultations.models import Consultation, ClinicalNote
from apps.consultations.serializers import ConsultationSerializer, ClinicalNoteSerializer
from apps.appointments.models import Appointment
from common.roles import UserRole
from common.permissions import IsDoctor
from common.responses import success_response, error_response


class ConsultationDetailView(APIView):
    """
    GET /api/v1/consultations/<id>/
    Fetch consultation session details and note.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, consultation_id):
        consultation = Consultation.objects.select_related(
            'appointment__doctor__user', 'appointment__patient__user'
        ).filter(id=consultation_id).first()

        if not consultation:
            return error_response(message="Consultation not found.", http_status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_participant = (
            consultation.appointment.patient.user == user or
            consultation.appointment.doctor.user == user or
            user.role == UserRole.ADMIN
        )
        if not is_participant:
            return error_response(message="Unauthorized to view this consultation.", http_status=status.HTTP_403_FORBIDDEN)

        serializer = ConsultationSerializer(consultation)
        return success_response(data=serializer.data)


class ConsultationEndView(APIView):
    """
    POST /api/v1/consultations/<id>/end/
    Marks consultation call as ended and marks appointment as completed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, consultation_id):
        consultation = Consultation.objects.select_related('appointment').filter(id=consultation_id).first()
        if not consultation:
            return error_response(message="Consultation not found.", http_status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_participant = (
            consultation.appointment.patient.user == user or
            consultation.appointment.doctor.user == user or
            user.role == UserRole.ADMIN
        )
        if not is_participant:
            return error_response(message="Unauthorized to end this consultation.", http_status=status.HTTP_403_FORBIDDEN)

        consultation.ended_at = timezone.now()
        consultation.status = Consultation.STATUS_COMPLETED
        consultation.save(update_fields=['ended_at', 'status', 'updated_at'])

        # Update appointment status to completed
        appointment = consultation.appointment
        appointment.status = Appointment.STATUS_COMPLETED
        appointment.save(update_fields=['status', 'updated_at'])

        return success_response(
            data=ConsultationSerializer(consultation).data,
            message="Consultation completed successfully."
        )


class ClinicalNoteCreateUpdateView(APIView):
    """
    POST /api/v1/consultations/<id>/notes/
    Allows the consulting doctor to create or update clinical notes.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def post(self, request, consultation_id):
        consultation = Consultation.objects.select_related('appointment__doctor__user').filter(id=consultation_id).first()
        if not consultation:
            return error_response(message="Consultation not found.", http_status=status.HTTP_404_NOT_FOUND)

        if consultation.appointment.doctor.user != request.user:
            return error_response(
                message="Only the attending doctor can author clinical notes for this encounter.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        note, created = ClinicalNote.objects.get_or_create(
            consultation=consultation,
            doctor=consultation.appointment.doctor,
            defaults={
                'chief_complaint': request.data.get('chief_complaint', ''),
                'clinical_observations': request.data.get('clinical_observations', ''),
                'diagnosis_summary': request.data.get('diagnosis_summary', ''),
                'treatment_advice': request.data.get('treatment_advice', ''),
            }
        )

        if not created:
            note.chief_complaint = request.data.get('chief_complaint', note.chief_complaint)
            note.clinical_observations = request.data.get('clinical_observations', note.clinical_observations)
            note.diagnosis_summary = request.data.get('diagnosis_summary', note.diagnosis_summary)
            note.treatment_advice = request.data.get('treatment_advice', note.treatment_advice)
            note.save()

        return success_response(
            data=ClinicalNoteSerializer(note).data,
            message="Clinical notes saved securely."
        )
