"""
Automated Tests for Doctor WhatsApp Notifications
Author: Communication & Quality Assurance Team
"""

import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from apps.accounts.models import User
from apps.doctors.models import DoctorProfile, Specialization
from apps.patients.models import PatientProfile
from apps.appointments.models import Appointment
from apps.notifications.models import Notification
from apps.notifications.services.whatsapp_service import WhatsAppService
from common.roles import UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user(
        email="dr.test.whatsapp@example.com",
        password="TestDoctorPass123!",
        first_name="Pooja",
        last_name="Iyer",
        phone_number="+91 98765 11111",
        role=UserRole.DOCTOR,
        is_email_verified=True,
    )
    spec, _ = Specialization.objects.get_or_create(name="General Medicine", slug="general-medicine")
    DoctorProfile.objects.create(
        user=user,
        specialization=spec,
        license_number="TEST-WA-001",
        whatsapp_number="+91 98765 11111",
        whatsapp_notifications_enabled=True,
        is_verified=True,
        consultation_fee=500.00
    )
    return user


@pytest.fixture
def patient_user(db):
    user = User.objects.create_user(
        email="patient.test.wa@example.com",
        password="TestPatientPass123!",
        first_name="Rohan",
        last_name="Kapoor",
        phone_number="+91 98765 22222",
        role=UserRole.PATIENT,
        is_email_verified=True,
    )
    PatientProfile.objects.create(user=user)
    return user


@pytest.mark.django_db
def test_clean_phone_number():
    assert WhatsAppService.clean_phone_number("9876543210") == "+919876543210"
    assert WhatsAppService.clean_phone_number("+91 98765-43210") == "+919876543210"
    assert WhatsAppService.clean_phone_number("+1 (415) 555-0123") == "+14155550123"


@pytest.mark.django_db
def test_appointment_booking_dispatches_whatsapp_to_doctor(api_client, doctor_user, patient_user):
    api_client.force_authenticate(user=patient_user)
    doctor = doctor_user.doctor_profile

    payload = {
        "doctor_id": str(doctor.id),
        "scheduled_date": "2026-11-15",
        "scheduled_time": "10:30:00",
        "reason_for_visit": "Persistent headache and fever for 3 days",
        "patient_symptoms_summary": "Mild fever, temples throbbing",
    }

    resp = api_client.post("/api/v1/appointments/", payload, format="json")
    assert resp.status_code == 201

    # Verify notification created in DB for doctor
    notif = Notification.objects.filter(user=doctor_user, notification_type=Notification.TYPE_APPOINTMENT).first()
    assert notif is not None
    assert "Persistent headache" in notif.message
    assert "Rohan Kapoor" in notif.message
    assert notif.whatsapp_status == "simulated"
    assert "https://wa.me/" in notif.metadata.get("wa_link", "")


@pytest.mark.django_db
def test_patient_joining_video_room_dispatches_whatsapp_to_doctor(api_client, doctor_user, patient_user):
    doctor = doctor_user.doctor_profile
    patient = patient_user.patient_profile

    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        scheduled_date=timezone.now().date(),
        scheduled_time=timezone.now().time(),
        reason_for_visit="Follow-up consultation",
        status=Appointment.STATUS_CONFIRMED,
        payment_status=Appointment.PAYMENT_PENDING,
        consultation_fee=500.00
    )

    api_client.force_authenticate(user=patient_user)
    resp = api_client.post(f"/api/v1/appointments/{appointment.id}/join/")
    assert resp.status_code == 200

    # Verify Video Call Notification created for doctor
    video_notif = Notification.objects.filter(user=doctor_user, notification_type=Notification.TYPE_VIDEOCALL).first()
    assert video_notif is not None
    assert "Video Call Starting Now" in video_notif.message
    assert f"/consultation/{appointment.id}" in video_notif.message


@pytest.mark.django_db
def test_doctor_update_whatsapp_preferences(api_client, doctor_user):
    api_client.force_authenticate(user=doctor_user)

    update_payload = {
        "whatsapp_number": "+91 99999 88888",
        "whatsapp_notifications_enabled": False,
    }
    resp = api_client.patch("/api/v1/doctors/me/", update_payload, format="json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["whatsapp_number"] == "+91 99999 88888"
    assert data["whatsapp_notifications_enabled"] is False


@pytest.mark.django_db
def test_manual_whatsapp_notify_endpoint(api_client, doctor_user, patient_user):
    doctor = doctor_user.doctor_profile
    patient = patient_user.patient_profile

    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        scheduled_date=timezone.now().date(),
        scheduled_time=timezone.now().time(),
        reason_for_visit="General checkup",
        status=Appointment.STATUS_CONFIRMED,
        consultation_fee=500.00
    )

    api_client.force_authenticate(user=doctor_user)
    resp = api_client.post(
        f"/api/v1/appointments/{appointment.id}/notify-whatsapp/",
        {"alert_type": "video_call"},
        format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["success"] is True
