"""
Hospital Serializers
Author: Emergency Response Infrastructure Team
"""

from rest_framework import serializers
from apps.hospitals.models import Hospital


class HospitalSerializer(serializers.ModelSerializer):
    distance_km = serializers.FloatField(required=False, read_only=True)
    directions_link = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = [
            'id',
            'name',
            'address',
            'city',
            'state',
            'postal_code',
            'phone_number',
            'emergency_phone',
            'latitude',
            'longitude',
            'has_emergency_room',
            'has_trauma_center',
            'has_icu',
            'is_24_7',
            'distance_km',
            'directions_link',
            'website',
        ]

    def get_directions_link(self, obj):
        if obj.latitude and obj.longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={obj.latitude},{obj.longitude}"
        return f"https://www.google.com/maps/search/?api=1&query={obj.name}+{obj.city}"


class NearbyHospitalSearchSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_blank=True, default="")
