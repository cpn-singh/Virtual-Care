"""
Appointment API Views
Author: Patient Care Operations Team

Coordinates appointment bookings, schedule adjustments, cancellation workflows,
and authorized entry into virtual consultation rooms.
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from django.conf import settings
from django.utils import timezone
from apps.appointments.models import Appointment
from apps.appointments.serializers import (
    AppointmentSerializer,
    BookAppointmentSerializer,
    CancelAppointmentSerializer,
    RescheduleAppointmentSerializer,
)
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.consultations.services.video_service import VideoService
from common.roles import UserRole
from common.responses import success_response, error_response


class AppointmentListCreateView(APIView):
    """
    GET /api/v1/appointments/
    POST /api/v1/appointments/
    List user appointments or book a new clinical consultation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == UserRole.PATIENT:
            appointments = Appointment.objects.filter(patient__user=user).select_related('doctor__user', 'doctor__specialization')
        elif user.role == UserRole.DOCTOR:
            appointments = Appointment.objects.filter(doctor__user=user).select_related('patient__user')
        elif user.role == UserRole.ADMIN:
            appointments = Appointment.objects.all().select_related('patient__user', 'doctor__user')
        else:
            appointments = Appointment.objects.none()

        serializer = AppointmentSerializer(appointments, many=True)
        return success_response(data=serializer.data)

    def post(self, request):
        if request.user.role != UserRole.PATIENT:
            return error_response(
                message="Only registered patients can book doctor appointments.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookAppointmentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Appointment booking validation failed.",
                errors=serializer.errors
            )

        doctor_id = serializer.validated_data['doctor_id']
        doctor_query = {'id': doctor_id}
        if not settings.DEBUG:
            doctor_query['is_verified'] = True
        doctor = DoctorProfile.objects.filter(**doctor_query).first()
        if not doctor:
            return error_response(
                message="The requested doctor was not found or is currently not verified for appointments.",
                http_status=status.HTTP_404_NOT_FOUND
            )

        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)

        appointment = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor,
            scheduled_date=serializer.validated_data['scheduled_date'],
            scheduled_time=serializer.validated_data['scheduled_time'],
            reason_for_visit=serializer.validated_data['reason_for_visit'],
            patient_symptoms_summary=serializer.validated_data.get('patient_symptoms_summary', ''),
            consultation_fee=doctor.consultation_fee,
            status=Appointment.STATUS_CONFIRMED,
            payment_status=Appointment.PAYMENT_PENDING
        )

        return success_response(
            data=AppointmentSerializer(appointment).data,
            message="Your appointment has been confirmed! You can complete payment anytime before the call.",
            http_status=status.HTTP_201_CREATED
        )


class AppointmentDetailView(APIView):
    """
    GET /api/v1/appointments/<id>/
    Object-level authorized appointment lookup.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, appointment_id):
        appointment = Appointment.objects.select_related(
            'doctor__user', 'doctor__specialization', 'patient__user'
        ).filter(id=appointment_id).first()

        if not appointment:
            return error_response(message="Appointment not found.", http_status=status.HTTP_404_NOT_FOUND)

        # Object-level permission check: must be patient, doctor, or admin
        user = request.user
        is_owner = (
            (user.role == UserRole.PATIENT and appointment.patient.user == user) or
            (user.role == UserRole.DOCTOR and appointment.doctor.user == user) or
            (user.role == UserRole.ADMIN)
        )
        if not is_owner:
            return error_response(
                message="You do not have permission to view this appointment record.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        return success_response(data=AppointmentSerializer(appointment).data)


class AppointmentCancelView(APIView):
    """
    POST /api/v1/appointments/<id>/cancel/
    Cancels an appointment if authorized.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, appointment_id):
        appointment = Appointment.objects.filter(id=appointment_id).first()
        if not appointment:
            return error_response(message="Appointment not found.", http_status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not (appointment.patient.user == user or appointment.doctor.user == user or user.role == UserRole.ADMIN):
            return error_response(message="Unauthorized to cancel this appointment.", http_status=status.HTTP_403_FORBIDDEN)

        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid()
        reason = serializer.validated_data.get('reason', '')

        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancellation_reason = reason
        appointment.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

        return success_response(
            data=AppointmentSerializer(appointment).data,
            message="Appointment cancelled successfully."
        )


class AppointmentRescheduleView(APIView):
    """
    POST /api/v1/appointments/<id>/reschedule/
    Adjusts the scheduled consultation date & time.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, appointment_id):
        appointment = Appointment.objects.filter(id=appointment_id).first()
        if not appointment:
            return error_response(message="Appointment not found.", http_status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not (appointment.patient.user == user or appointment.doctor.user == user or user.role == UserRole.ADMIN):
            return error_response(message="Unauthorized to reschedule this appointment.", http_status=status.HTTP_403_FORBIDDEN)

        serializer = RescheduleAppointmentSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        appointment.scheduled_date = serializer.validated_data['scheduled_date']
        appointment.scheduled_time = serializer.validated_data['scheduled_time']
        appointment.status = Appointment.STATUS_RESCHEDULED
        appointment.save(update_fields=['scheduled_date', 'scheduled_time', 'status', 'updated_at'])

        return success_response(
            data=AppointmentSerializer(appointment).data,
            message="Appointment rescheduled successfully."
        )


class AppointmentJoinView(APIView):
    """
    POST /api/v1/appointments/<id>/join/
    Authenticates and issues short-lived video room credentials for doctor or patient.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, appointment_id):
        appointment = Appointment.objects.select_related(
            'doctor__user', 'patient__user'
        ).filter(id=appointment_id).first()

        if not appointment:
            return error_response(message="Appointment not found.", http_status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_participant = (appointment.patient.user == user or appointment.doctor.user == user or user.role == UserRole.ADMIN)
        if not is_participant:
            return error_response(
                message="You are not authorized to join this consultation room.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        if appointment.status == Appointment.STATUS_CANCELLED:
            return error_response(
                message="This appointment was cancelled and cannot be joined.",
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Update appointment status to in_progress if starting
        if appointment.status in (Appointment.STATUS_CONFIRMED, Appointment.STATUS_RESCHEDULED, Appointment.STATUS_PENDING):
            appointment.status = Appointment.STATUS_IN_PROGRESS
            appointment.save(update_fields=['status', 'updated_at'])

        # Create or fetch consultation room
        consultation = VideoService.get_or_create_room(appointment)
        if not consultation.started_at:
            consultation.started_at = timezone.now()
            consultation.status = 'active'
            consultation.save(update_fields=['started_at', 'status'])

        credentials = VideoService.generate_access_credentials(consultation, user)

        return success_response(
            data={
                "consultation_id": consultation.id,
                "appointment_id": appointment.id,
                "credentials": credentials,
                "patient_name": appointment.patient.user.full_name,
                "doctor_name": appointment.doctor.user.full_name,
            },
            message="Room access authorized."
        )
