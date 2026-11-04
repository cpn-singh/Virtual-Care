"""
Doctor API Views
Author: Clinical Operations Team

Endpoints for:
- Doctor directory discovery with search & filter
- Doctor public profile & schedule slots
- Doctor self-management of bio and availability
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from django.conf import settings
from django.db.models import Q
from apps.doctors.models import DoctorProfile, Specialization, DoctorAvailability
from apps.doctors.serializers import (
    DoctorPublicListSerializer,
    DoctorProfileMeSerializer,
    SpecializationSerializer,
    DoctorAvailabilitySerializer,
)
from apps.accounts.models import User
from common.roles import UserRole
from common.permissions import IsDoctor
from common.responses import success_response, error_response


class SpecializationListView(APIView):
    """
    GET /api/v1/doctors/specializations/
    Returns list of medical specialties (Cardiology, Dermatology, Pediatrics, etc.).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        specialties = Specialization.objects.all()
        serializer = SpecializationSerializer(specialties, many=True)
        return success_response(data=serializer.data)


class DoctorListView(APIView):
    """
    GET /api/v1/doctors/
    Searchable doctor directory.
    Query parameters:
    - ?search=Dr+John
    - ?specialization=cardiology
    - ?city=Mumbai
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = DoctorProfile.objects.select_related('user', 'specialization').filter(
            user__is_active=True,
            is_available_for_telehealth=True
        )
        if not settings.DEBUG:
            queryset = queryset.filter(is_verified=True)

        search_query = request.query_params.get('search', '').strip()
        if search_query and search_query.lower() != 'undefined':
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(specialization__name__icontains=search_query) |
                Q(bio__icontains=search_query)
            )

        specialization_slug = request.query_params.get('specialization', '').strip()
        if specialization_slug and specialization_slug.lower() != 'undefined':
            queryset = queryset.filter(specialization__slug=specialization_slug)

        city = request.query_params.get('city', '').strip()
        if city and city.lower() != 'undefined':
            queryset = queryset.filter(city__icontains=city)

        serializer = DoctorPublicListSerializer(queryset, many=True)
        return success_response(data=serializer.data)


class DoctorDetailView(APIView):
    """
    GET /api/v1/doctors/<id>/
    Public profile of an individual doctor.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, doctor_id):
        doctor = DoctorProfile.objects.select_related('user', 'specialization').filter(id=doctor_id).first()
        if not doctor:
            return error_response(message="Doctor not found.", http_status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorPublicListSerializer(doctor)
        return success_response(data=serializer.data)


class DoctorAvailabilityListView(APIView):
    """
    GET /api/v1/doctors/<id>/availability/
    Retrieves weekly consultation schedule for booking.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, doctor_id):
        doctor = DoctorProfile.objects.filter(id=doctor_id).first()
        if not doctor:
            return error_response(message="Doctor not found.", http_status=status.HTTP_404_NOT_FOUND)

        slots = DoctorAvailability.objects.filter(doctor=doctor, is_active=True)
        serializer = DoctorAvailabilitySerializer(slots, many=True)
        return success_response(data=serializer.data)


class DoctorProfileMeView(APIView):
    """
    GET /api/v1/doctors/me/profile/
    PATCH /api/v1/doctors/me/profile/
    Allows logged-in doctor to view and manage their profile details.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def get(self, request):
        doctor_profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorProfileMeSerializer(doctor_profile)
        return success_response(data=serializer.data)

    def patch(self, request):
        doctor_profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorProfileMeSerializer(doctor_profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Doctor profile updated successfully."
        )


class DoctorMeAvailabilityView(APIView):
    """
    POST /api/v1/doctors/me/availability/
    Allows doctor to add or update consultation time slots.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor_profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorAvailabilitySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        slot = serializer.save(doctor=doctor_profile)
        return success_response(
            data=DoctorAvailabilitySerializer(slot).data,
            message="Availability slot added successfully.",
            http_status=status.HTTP_201_CREATED
        )


class AdminDoctorCreateView(APIView):
    """
    POST /api/v1/doctors/admin-create/
    Enforces that only platform administrators can onboard and credential doctors
    with complete professional profile and clinical descriptions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != UserRole.ADMIN:
            return error_response(
                message="Only platform administrators have permission to provision and credential doctors.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        email = data.get('email', '').lower().strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        password = data.get('password', 'Doctor@2026!').strip()
        phone_number = data.get('phone_number', '').strip()
        specialization_id = data.get('specialization_id')
        qualifications = data.get('qualifications', 'MBBS').strip()
        license_number = data.get('license_number', '').strip()
        experience_years = int(data.get('experience_years', 5))
        consultation_fee = data.get('consultation_fee', 500.00)
        city = data.get('city', '').strip()
        clinic_address = data.get('clinic_address', '').strip()
        bio = data.get('bio', '').strip()

        if not email or not first_name or not last_name:
            return error_response(
                message="Email, first name, and last name are required.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return error_response(
                message=f"An account with email {email} already exists.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Create User account with DOCTOR role
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=UserRole.DOCTOR,
            is_email_verified=True,
            is_active=True
        )

        # 2. Resolve specialization
        specialization = None
        if specialization_id:
            specialization = Specialization.objects.filter(id=specialization_id).first()
        if not specialization:
            specialization = Specialization.objects.filter(slug='general-medicine').first()

        # 3. Create DoctorProfile with full description & verified status
        doctor_profile = DoctorProfile.objects.create(
            user=user,
            specialization=specialization,
            qualifications=qualifications,
            license_number=license_number,
            experience_years=experience_years,
            consultation_fee=consultation_fee,
            city=city,
            clinic_address=clinic_address,
            bio=bio,
            is_verified=True,
            is_available_for_telehealth=True
        )

        # 4. Standard availability slots (Mon-Fri 09:00 - 17:00)
        for day in range(5):
            DoctorAvailability.objects.create(
                doctor=doctor_profile,
                day_of_week=day,
                start_time='09:00:00',
                end_time='17:00:00',
                slot_duration_minutes=30,
                is_active=True
            )

        serializer = DoctorPublicListSerializer(doctor_profile)
        return success_response(
            data=serializer.data,
            message=f"Dr. {user.full_name} has been credentialed and added successfully with proper clinical profile.",
            http_status=status.HTTP_201_CREATED
        )
