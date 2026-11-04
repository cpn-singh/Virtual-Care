"""
Consultation Serializers
Author: Telehealth Video & Media Team
"""

from rest_framework import serializers
from apps.consultations.models import Consultation, ClinicalNote
from apps.appointments.serializers import AppointmentSerializer


class ClinicalNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalNote
        fields = [
            'id',
            'chief_complaint',
            'clinical_observations',
            'diagnosis_summary',
            'treatment_advice',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConsultationSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    clinical_note = ClinicalNoteSerializer(read_only=True)

    class Meta:
        model = Consultation
        fields = [
            'id',
            'appointment',
            'room_id',
            'status',
            'started_at',
            'ended_at',
            'clinical_note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'room_id', 'created_at', 'updated_at']
