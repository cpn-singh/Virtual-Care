"""
Doctor Serializers
Author: Clinical Operations Team
"""

from rest_framework import serializers
from apps.doctors.models import Specialization, DoctorProfile, DoctorAvailability
from apps.accounts.serializers import UserSummarySerializer


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'slug', 'description', 'icon_name']


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorAvailability
        fields = [
            'id',
            'day_of_week',
            'day_name',
            'start_time',
            'end_time',
            'slot_duration_minutes',
            'is_active',
        ]


class DoctorPublicListSerializer(serializers.ModelSerializer):
    """Clean serializer for public discovery."""
    user = UserSummarySerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'id',
            'user',
            'specialization',
            'qualifications',
            'experience_years',
            'bio',
            'city',
            'consultation_fee',
            'is_verified',
            'is_available_for_telehealth',
            'rating',
            'total_consultations',
        ]


class DoctorProfileMeSerializer(serializers.ModelSerializer):
    """Full serializer for doctor's own dashboard."""
    user = UserSummarySerializer(read_only=True)
    specialization_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    specialization = SpecializationSerializer(read_only=True)
    availability_slots = DoctorAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'id',
            'user',
            'specialization',
            'specialization_id',
            'license_number',
            'qualifications',
            'experience_years',
            'bio',
            'clinic_address',
            'city',
            'consultation_fee',
            'is_verified',
            'is_available_for_telehealth',
            'rating',
            'total_consultations',
            'availability_slots',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'rating', 'total_consultations', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        spec_id = validated_data.pop('specialization_id', None)
        if spec_id:
            instance.specialization = Specialization.objects.filter(id=spec_id).first()
        return super().update(instance, validated_data)
