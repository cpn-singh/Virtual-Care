"""
Tests for Doctor AI Email Generation, Provisioning, and Dual-Login
Author: Clinical Operations & Systems Architecture
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from common.roles import UserRole
from apps.doctors.models import DoctorProfile
from apps.doctors.services.doctor_ai_email_service import DoctorAIEmailService

User = get_user_model()


@pytest.mark.django_db
class TestDoctorAIEmailGeneration:
    def test_clean_handle_and_domain_generation(self):
        result = DoctorAIEmailService.generate_careconnect_email("Rachna", "Sheikh")
        assert result["primary_email"] == "dr.rachna.sheikh@careconnect.health"
        assert result["domain"] == "careconnect.health"

    def test_special_characters_and_whitespace_sanitization(self):
        result = DoctorAIEmailService.generate_careconnect_email("Dr. M. K. ", "O'Connor-Smith")
        email = result["primary_email"]
        assert email.endswith("@careconnect.health")
        assert email.startswith("dr.")
        assert " " not in email
        assert "'" not in email

    def test_collision_resolution(self):
        # Create an existing user and doctor with dr.same.name@careconnect.health
        user1 = User.objects.create_user(
            email="dr.same.name@careconnect.health",
            password="TestPassword123!",
            role=UserRole.DOCTOR,
            first_name="Same",
            last_name="Name",
        )
        DoctorProfile.objects.create(
            user=user1,
            careconnect_email="dr.same.name@careconnect.health",
            qualifications="MBBS",
            experience_years=5,
            consultation_fee=500,
        )

        # Generating another email for Same Name should resolve collision with alternative or numeric suffix
        collision_resolved = DoctorAIEmailService.generate_careconnect_email("Same", "Name")
        assert collision_resolved["primary_email"] != "dr.same.name@careconnect.health"
        assert collision_resolved["primary_email"].endswith("@careconnect.health")


@pytest.mark.django_db
class TestDoctorMailboxProvisioningAndForwarding:
    def test_provision_and_forwarding(self):
        user = User.objects.create_user(
            email="clinician.personal@gmail.com",
            password="SecureDoctor2026!",
            role=UserRole.DOCTOR,
            first_name="Sunita",
            last_name="Rao",
        )
        doctor = DoctorProfile.objects.create(
            user=user,
            personal_email="clinician.personal@gmail.com",
            qualifications="MBBS, MS",
            experience_years=8,
            consultation_fee=700,
        )

        provision_result = DoctorAIEmailService.provision_doctor_mailbox(
            doctor,
            careconnect_email="dr.sunita.rao@careconnect.health",
            send_welcome_alert=False,
        )
        doctor.refresh_from_db()

        assert provision_result["success"] is True
        assert doctor.careconnect_email == "dr.sunita.rao@careconnect.health"
        assert doctor.email_forwarding_enabled is True
        assert doctor.email_provisioned_at is not None

        # Test forwarding
        forward_ok = DoctorAIEmailService.forward_careconnect_email(
            to_careconnect_email="dr.sunita.rao@careconnect.health",
            subject="New Telehealth Appointment",
            message="Patient booked 10:00 AM slot.",
        )
        assert forward_ok is True


@pytest.mark.django_db
class TestDualLoginWithCareConnectEmail:
    def test_login_with_both_personal_and_careconnect_email(self):
        client = APIClient()
        user = User.objects.create_user(
            email="dr.kavita.personal@example.com",
            password="SecretPassword2026!",
            role=UserRole.DOCTOR,
            first_name="Kavita",
            last_name="Iyer",
            is_email_verified=True,
        )
        DoctorProfile.objects.create(
            user=user,
            careconnect_email="dr.kavita.iyer@careconnect.health",
            personal_email="dr.kavita.personal@example.com",
            qualifications="MBBS, MD",
            experience_years=10,
            consultation_fee=800,
        )

        # 1. Login with official CareConnect email
        login_official = client.post(
            "/api/v1/auth/login/",
            {"email": "dr.kavita.iyer@careconnect.health", "password": "SecretPassword2026!"},
            format="json",
        )
        assert login_official.status_code == 200
        assert "token" in login_official.data["data"]

        # 2. Login with personal forwarding email
        login_personal = client.post(
            "/api/v1/auth/login/",
            {"email": "dr.kavita.personal@example.com", "password": "SecretPassword2026!"},
            format="json",
        )
        assert login_personal.status_code == 200
        assert "token" in login_personal.data["data"]


@pytest.mark.django_db
class TestAIEmailEndpoints:
    def test_ai_generate_email_endpoint(self):
        client = APIClient()
        admin = User.objects.create_user(
            email="admin.ops@careconnect.local",
            password="AdminPass2026!",
            role=UserRole.ADMIN,
            first_name="Admin",
            last_name="Ops",
        )
        client.force_authenticate(user=admin)

        response = client.post(
            "/api/v1/doctors/ai-generate-email/",
            {"first_name": "Deepak", "last_name": "Verma"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["data"]["primary_email"] == "dr.deepak.verma@careconnect.health"

    def test_admin_create_doctor_auto_email(self):
        client = APIClient()
        admin = User.objects.create_user(
            email="admin.ops2@careconnect.local",
            password="AdminPass2026!",
            role=UserRole.ADMIN,
            first_name="Super",
            last_name="Admin",
        )
        client.force_authenticate(user=admin)

        response = client.post(
            "/api/v1/doctors/admin-create/",
            {
                "first_name": "Meera",
                "last_name": "Choudhury",
                "email": "meera.personal@yahoo.com",
                "password": "DoctorPass2026!",
                "qualifications": "MBBS, DNB",
                "experience_years": 7,
                "consultation_fee": 650,
                "bio": "Experienced cardiologist focused on hypertension.",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.data["data"]
        assert data["careconnect_email"] == "dr.meera.choudhury@careconnect.health"
        assert data["personal_email"] == "meera.personal@yahoo.com"
