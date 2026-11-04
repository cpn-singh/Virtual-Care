"""
Prescription API Views
Author: Clinical Pharmacy & Governance Team

Endpoints for:
- Viewing patient prescription history
- Doctor authoring & finalization of digital prescriptions
- Generating official, tamper-evident PDF prescription downloads
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from apps.prescriptions.models import Prescription, PrescriptionItem
from apps.prescriptions.serializers import (
    PrescriptionSerializer,
    CreatePrescriptionSerializer,
)
from apps.prescriptions.services.pdf_generator import generate_prescription_pdf
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.appointments.models import Appointment
from apps.consultations.models import Consultation
from common.roles import UserRole
from common.permissions import IsDoctor
from common.responses import success_response, error_response


class PrescriptionListCreateView(APIView):
    """
    GET /api/v1/prescriptions/
    POST /api/v1/prescriptions/
    List user prescriptions or author a new prescription.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == UserRole.PATIENT:
            prescriptions = Prescription.objects.filter(patient__user=user).select_related('doctor__user', 'doctor__specialization')
        elif user.role == UserRole.DOCTOR:
            prescriptions = Prescription.objects.filter(doctor__user=user).select_related('patient__user')
        elif user.role == UserRole.ADMIN:
            prescriptions = Prescription.objects.all().select_related('patient__user', 'doctor__user')
        else:
            prescriptions = Prescription.objects.none()

        serializer = PrescriptionSerializer(prescriptions, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        # Strict clinical rule: only doctors can create prescriptions
        if request.user.role != UserRole.DOCTOR:
            return error_response(
                message="Only licensed clinicians are authorized to author medical prescriptions.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        doctor_profile = DoctorProfile.objects.filter(user=request.user).first()
        if not doctor_profile or not doctor_profile.is_verified:
            return error_response(
                message="Doctor credentials must be verified before issuing prescriptions.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreatePrescriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        patient = PatientProfile.objects.filter(id=serializer.validated_data['patient_id']).first()
        if not patient:
            return error_response(message="Patient not found.", http_status=status.HTTP_404_NOT_FOUND)

        appointment = None
        if serializer.validated_data.get('appointment_id'):
            appointment = Appointment.objects.filter(id=serializer.validated_data['appointment_id']).first()

        consultation = None
        if serializer.validated_data.get('consultation_id'):
            consultation = Consultation.objects.filter(id=serializer.validated_data['consultation_id']).first()

        # Create prescription record
        prescription = Prescription.objects.create(
            patient=patient,
            doctor=doctor_profile,
            appointment=appointment,
            consultation=consultation,
            diagnosis=serializer.validated_data['diagnosis'],
            doctor_notes=serializer.validated_data.get('doctor_notes', ''),
            status=Prescription.STATUS_ISSUED,  # Finalized on issue
            issued_at=timezone.now()
        )

        # Add medication items
        for item_data in serializer.validated_data.get('items', []):
            PrescriptionItem.objects.create(prescription=prescription, **item_data)

        return success_response(
            data=PrescriptionSerializer(prescription).data,
            message="Prescription created and signed successfully.",
            http_status=status.HTTP_201_CREATED
        )


class PrescriptionDetailView(APIView):
    """
    GET /api/v1/prescriptions/<id>/
    Fetch single prescription record.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, prescription_id):
        prescription = Prescription.objects.select_related(
            'doctor__user', 'doctor__specialization', 'patient__user'
        ).filter(id=prescription_id).first()

        if not prescription:
            return error_response(message="Prescription not found.", http_status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_authorized = (
            prescription.patient.user == user or
            prescription.doctor.user == user or
            user.role == UserRole.ADMIN
        )
        if not is_authorized:
            return error_response(message="Unauthorized to view this prescription.", http_status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(prescription)
        return success_response(data=serializer.data)


class PrescriptionPDFView(APIView):
    """
    GET /api/v1/prescriptions/<id>/pdf/
    Generates or streams the official clinician-signed PDF.
    Supports either standard Authorization header or ?token=<token> in query params
    so users can view and download PDFs directly in a browser tab.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, prescription_id):
        # 1. Resolve user from request.user, query param token, or header
        user = request.user if (request.user and request.user.is_authenticated) else None

        if not user:
            token = request.query_params.get('token')
            if token:
                from apps.accounts.models import AuthToken, User
                auth_tok = AuthToken.objects.filter(key=token).select_related('user').first()
                if auth_tok and not auth_tok.is_expired():
                    user = auth_tok.user
                else:
                    try:
                        from rest_framework_simplejwt.tokens import AccessToken
                        decoded = AccessToken(token)
                        user = User.objects.filter(id=decoded.get('user_id')).first()
                    except Exception:
                        user = None

        if not user or not user.is_authenticated:
            # In development mode, if a user/developer opens the URL directly in a browser address bar,
            # allow streaming the PDF for the existing prescription
            if settings.DEBUG:
                rx_check = Prescription.objects.select_related('patient__user').filter(id=prescription_id).first()
                if rx_check and rx_check.patient and rx_check.patient.user:
                    user = rx_check.patient.user

            if not user or not user.is_authenticated:
                return error_response(
                    message="Authentication credentials were not provided. Please provide an active session token.",
                    http_status=status.HTTP_401_UNAUTHORIZED
                )

        prescription = Prescription.objects.select_related(
            'doctor__user', 'doctor__specialization', 'patient__user'
        ).filter(id=prescription_id).first()

        if not prescription:
            return error_response(message="Prescription not found.", http_status=status.HTTP_404_NOT_FOUND)

        is_authorized = (
            prescription.patient.user == user or
            prescription.doctor.user == user or
            user.role == UserRole.ADMIN
        )
        if not is_authorized:
            return error_response(message="Unauthorized to download this prescription.", http_status=status.HTTP_403_FORBIDDEN)

        try:
            pdf_bytes = generate_prescription_pdf(prescription)
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            # Inline disposition lets modern browser PDF viewers preview cleanly in a new tab
            response['Content-Disposition'] = f'inline; filename="Prescription-{str(prescription.id)[:8]}.pdf"'
            return response
        except Exception as e:
            return error_response(
                message=f"Failed to generate prescription PDF: {str(e)}",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
