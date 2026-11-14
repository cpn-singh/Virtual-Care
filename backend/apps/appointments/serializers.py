"""
Appointment Serializers
Author: Patient Care Operations Team
"""

from rest_framework import serializers
from apps.appointments.models import Appointment
from apps.doctors.serializers import DoctorPublicListSerializer
from apps.patients.serializers import PatientProfileSerializer
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile


class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorPublicListSerializer(read_only=True)
    patient = PatientProfileSerializer(read_only=True)
    doctor_whatsapp_link = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            'status',
            'payment_status',
            'consultation_fee',
            'reason_for_visit',
            'patient_symptoms_summary',
            'cancellation_reason',
            'doctor_whatsapp_link',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'payment_status', 'created_at', 'updated_at']

    def get_doctor_whatsapp_link(self, obj) -> str:
        if not obj.doctor:
            return ""
        phone = obj.doctor.effective_whatsapp_number
        if not phone:
            return ""
        from apps.notifications.services.whatsapp_service import WhatsAppService
        patient_name = obj.patient.user.full_name if obj.patient else "Patient"
        msg = (
            f"🏥 *Virtual Care Appointment Query*\n"
            f"Dr. {obj.doctor.user.full_name}, regarding appointment #{str(obj.id)[:8]} "
            f"with patient {patient_name} scheduled for {obj.scheduled_date} at {obj.scheduled_time}."
        )
        return WhatsAppService.generate_wa_deep_link(phone, msg)


class BookAppointmentSerializer(serializers.Serializer):
    """Payload to schedule a new consultation."""
    doctor_id = serializers.UUIDField()
    scheduled_date = serializers.DateField()
    scheduled_time = serializers.TimeField()
    reason_for_visit = serializers.CharField(max_length=1000)
    patient_symptoms_summary = serializers.CharField(required=False, allow_blank=True, default="")


class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class RescheduleAppointmentSerializer(serializers.Serializer):
    scheduled_date = serializers.DateField()
    scheduled_time = serializers.TimeField()
