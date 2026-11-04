"""
Patient API Views
Author: Clinical Systems Engineering Team
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from apps.patients.models import PatientProfile
from apps.patients.serializers import PatientProfileSerializer
from common.permissions import IsPatient
from common.responses import success_response, error_response


class PatientProfileMeView(APIView):
    """
    GET /api/v1/patients/me/
    PATCH /api/v1/patients/me/
    Manage the logged-in patient's health profile, allergies, and emergency contacts.
    """
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile)
        return success_response(data=serializer.data)

    def patch(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                message="Profile update failed.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Health profile updated successfully."
        )
