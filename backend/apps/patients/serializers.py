"""
Patient Profile Serializers
Author: Clinical Systems Engineering Team
"""

from rest_framework import serializers
from apps.patients.models import PatientProfile
from apps.accounts.serializers import UserSummarySerializer


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'user',
            'date_of_birth',
            'gender',
            'blood_group',
            'address',
            'city',
            'state',
            'postal_code',
            'allergies',
            'chronic_conditions',
            'current_medications',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'consent_ai_triage',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
