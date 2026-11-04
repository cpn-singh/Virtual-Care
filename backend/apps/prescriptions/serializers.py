"""
Prescription Serializers
Author: Clinical Pharmacy & Governance Team
"""

from rest_framework import serializers
from apps.prescriptions.models import Prescription, PrescriptionItem
from apps.doctors.serializers import DoctorPublicListSerializer
from apps.patients.serializers import PatientProfileSerializer


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = [
            'id',
            'medicine_name',
            'formulation',
            'strength',
            'dose',
            'frequency',
            'duration',
            'instructions',
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    doctor = DoctorPublicListSerializer(read_only=True)
    patient = PatientProfileSerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id',
            'patient',
            'doctor',
            'appointment',
            'consultation',
            'status',
            'diagnosis',
            'doctor_notes',
            'version',
            'issued_at',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'version', 'issued_at', 'created_at', 'updated_at']


class CreatePrescriptionSerializer(serializers.Serializer):
    appointment_id = serializers.UUIDField(required=False, allow_null=True)
    consultation_id = serializers.UUIDField(required=False, allow_null=True)
    patient_id = serializers.UUIDField()
    diagnosis = serializers.CharField(max_length=2000)
    doctor_notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = PrescriptionItemSerializer(many=True, required=False, default=[])
