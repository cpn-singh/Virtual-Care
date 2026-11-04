"""
Hospital Locator API Views
Author: Emergency Response Infrastructure Team

Provides nearby emergency center discovery with offline fallback,
distance calculation, and guaranteed emergency phone number delivery.
"""

import math
from rest_framework.views import APIView
from rest_framework import permissions, status
from django.conf import settings
from apps.hospitals.models import Hospital
from apps.hospitals.serializers import HospitalSerializer, NearbyHospitalSearchSerializer
from common.responses import success_response, error_response


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class NearbyHospitalsView(APIView):
    """
    POST /api/v1/hospitals/nearby/
    Finds hospitals with emergency departments.
    Available to anyone without login for immediate patient safety.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = NearbyHospitalSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        user_lat = serializer.validated_data.get('latitude')
        user_lon = serializer.validated_data.get('longitude')
        city_filter = serializer.validated_data.get('city', '').strip()

        hospitals = list(Hospital.objects.filter(has_emergency_room=True))

        # Seed defaults if database is currently empty
        if not hospitals:
            Hospital.objects.create(
                name="AIIMS New Delhi Emergency Department",
                address="Sri Aurobindo Marg, Ansari Nagar",
                city="New Delhi",
                state="Delhi",
                phone_number="+91 11 2658 8500",
                emergency_phone="112",
                latitude=28.5672,
                longitude=77.2100,
                has_emergency_room=True,
                has_trauma_center=True,
                is_24_7=True
            )
            Hospital.objects.create(
                name="KEM Hospital & Emergency Center",
                address="Acharya Donde Marg, Parel",
                city="Mumbai",
                state="Maharashtra",
                phone_number="+91 22 2410 7000",
                emergency_phone="112",
                latitude=19.0024,
                longitude=72.8427,
                has_emergency_room=True,
                has_trauma_center=True,
                is_24_7=True
            )
            Hospital.objects.create(
                name="Victoria Hospital Emergency Care",
                address="Fort Road, near City Market",
                city="Bengaluru",
                state="Karnataka",
                phone_number="+91 80 2670 1150",
                emergency_phone="112",
                latitude=12.9625,
                longitude=77.5746,
                has_emergency_room=True,
                has_trauma_center=True,
                is_24_7=True
            )
            hospitals = list(Hospital.objects.filter(has_emergency_room=True))

        # Filter by city if specified
        if city_filter:
            filtered = [h for h in hospitals if city_filter.lower() in h.city.lower()]
            if filtered:
                hospitals = filtered

        # If user coordinates are provided, compute distance and sort
        results = []
        if user_lat is not None and user_lon is not None:
            for h in hospitals:
                if h.latitude and h.longitude:
                    dist = haversine_distance(user_lat, user_lon, h.latitude, h.longitude)
                else:
                    dist = 999.0
                h.distance_km = dist
                results.append(h)
            results.sort(key=lambda x: getattr(x, 'distance_km', 999.0))
        else:
            results = hospitals

        serialized_data = HospitalSerializer(results[:15], many=True).data

        return success_response(
            data={
                "emergency_numbers": {
                    "general_emergency": settings.EMERGENCY_PHONE_NUMBER,
                    "ambulance": settings.AMBULANCE_PHONE_NUMBER,
                },
                "hospitals": serialized_data,
                "disclaimer": "Emergency availability and ICU bed capacity must be verified directly with the hospital. If you are in immediate life-threatening danger, dial 112."
            },
            message="Emergency hospital directory retrieved."
        )
