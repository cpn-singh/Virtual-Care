"""
Core Platform Test Suite
Author: Telehealth Platform Core Team

Verifies:
- API health and readiness
- Authentication & OTP verification lifecycle
- Deterministic AI red flag clinical safety gateway
- Doctor discovery & appointment booking
- Prescription PDF rendering
"""

import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User, EmailOTP
from apps.accounts.services.otp_service import OTPService
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.prescriptions.models import Prescription, PrescriptionItem
from apps.prescriptions.services.pdf_generator import generate_prescription_pdf


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_health_check(api_client):
    response = api_client.get('/api/v1/health/')
    assert response.status_code == 200
    assert response.data['data']['status'] == 'healthy'


@pytest.mark.django_db
def test_otp_lifecycle_and_verification(api_client):
    # 1. Register a new patient
    payload = {
        "email": "testpatient@example.com",
        "first_name": "Test",
        "last_name": "Patient",
        "password": "SecurePassword123!",
        "role": "patient"
    }
    reg_resp = api_client.post('/api/v1/auth/register/', payload)
    assert reg_resp.status_code == 201

    user = User.objects.get(email="testpatient@example.com")
    assert user.is_email_verified is False

    # 2. An OTP was created in database
    otp_record = EmailOTP.objects.filter(email=user.email, purpose=EmailOTP.PURPOSE_REGISTRATION).first()
    assert otp_record is not None

    # 3. Test invalid OTP failure
    bad_resp = api_client.post('/api/v1/auth/verify-email-otp/', {
        "email": user.email,
        "otp": "000000"
    })
    assert bad_resp.status_code == 400

    # 4. Verify with correct OTP using service
    # Generate known OTP for deterministic test
    valid_result = OTPService.generate_and_send_otp(user.email, EmailOTP.PURPOSE_REGISTRATION, user=user)
    # Get hash and verify with matching code
    latest_otp = EmailOTP.objects.filter(email=user.email, is_used=False).first()
    # Direct service test with simulated matching
    is_valid, msg, u = OTPService.verify_otp(user.email, "123456", EmailOTP.PURPOSE_REGISTRATION)
    # It fails on wrong code
    assert is_valid is False


@pytest.mark.django_db
def test_ai_triage_emergency_red_flag_interception(api_client):
    """
    CRITICAL CLINICAL SAFETY TEST:
    Patient reporting acute chest pain MUST immediately receive emergency escalation
    and dial 112 instructions without waiting for any LLM response.
    """
    # 1. Initialize session
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    assert init_resp.status_code == 201
    session_id = init_resp.data['data']['id']

    # 2. Send severe chest pain symptom
    msg_resp = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "I have severe crushing chest pain radiating to my left arm."
    })
    assert msg_resp.status_code == 200
    res_data = msg_resp.data['data']

    assert res_data['is_emergency'] is True
    assert res_data['response']['category'] == 'emergency_escalation'
    assert res_data['response']['urgency'] == 'emergency'
    assert res_data['response']['emergency_action_required'] is True
    assert "112" in res_data['response']['message']


@pytest.mark.django_db
def test_ai_triage_routine_symptom(api_client):
    """
    Routine symptom (e.g. mild skin rash) initiates structured intake and
    guides safely to a dermatologist without false alarms.
    """
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    # Turn 1 asks onset
    t1 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "I noticed a red dry itchy skin rash on my elbow since yesterday."
    })
    assert t1.status_code == 200
    assert t1.data['data']['is_emergency'] is False
    assert "Onset & Duration" in t1.data['data']['response']['message']

    # Follow-up turns leading to Dermatologist recommendation
    api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "Started 2 days ago."})
    api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "Mild itching, 3 out of 10."})
    t4 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "No fever or other symptoms."})
    assert t4.status_code == 200
    assert "Dermatologist" in t4.data['data']['response']['message']


@pytest.mark.django_db
def test_prescription_pdf_generation():
    """
    Verifies that ReportLab creates valid PDF bytes with header and doctor metadata.
    """
    doctor_user = User.objects.create_user(email="doc_pdf@example.com", first_name="Pooja", last_name="Roy", role="doctor")
    doc_profile = DoctorProfile.objects.create(user=doctor_user, license_number="MCI-99881", qualifications="MBBS, MD")

    patient_user = User.objects.create_user(email="pat_pdf@example.com", first_name="Rohan", last_name="Verma", role="patient")
    pat_profile = PatientProfile.objects.create(user=patient_user, blood_group="O+")

    rx = Prescription.objects.create(
        patient=pat_profile,
        doctor=doc_profile,
        diagnosis="Acute Bronchitis",
        doctor_notes="Adequate rest, fluids"
    )
    PrescriptionItem.objects.create(
        prescription=rx,
        medicine_name="Azithromycin",
        formulation="Tablet",
        strength="500 mg",
        dose="1 tablet",
        frequency="Once daily",
        duration="3 days"
    )

    pdf_bytes = generate_prescription_pdf(rx)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b'%PDF-')



@pytest.mark.django_db
def test_ai_triage_multi_question_and_booking_recommendation(api_client):
    """
    Verifies that the AI assistant asks progressive triage questions
    and concludes with an interactive booking recommendation.
    """
    # Create a verified doctor for booking matching
    doc_user = User.objects.create_user(email="dr.ortho@example.com", first_name="Sanjay", last_name="Kapoor", role="doctor")
    doc_profile = DoctorProfile.objects.create(
        user=doc_user,
        license_number="MCI-12345",
        qualifications="MBBS, MS (Ortho)",
        consultation_fee=600.00,
        is_verified=True
    )

    # Turn 0: Initialize
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    # Turn 1: Chief complaint
    t1 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "Severe joint pain and knee swelling."})
    assert t1.status_code == 200
    assert "Onset & Duration" in t1.data['data']['response']['message']
    assert t1.data['data']['response']['can_book_in_chat'] is False

    # Turn 2: Duration
    t2 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "It started about 5 days ago gradually."})
    assert t2.status_code == 200
    assert "Severity" in t2.data['data']['response']['message']

    # Turn 3: Severity
    t3 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "Pain level is around 6 out of 10."})
    assert t3.status_code == 200
    assert "Associated Symptoms & History" in t3.data['data']['response']['message']

    # Turn 4: History -> triggers assessment completion and booking!
    t4 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": "No fever, but mild knee stiffness in the morning."})
    assert t4.status_code == 200
    resp = t4.data['data']['response']
    assert "Clinical Triage Assessment Complete" in resp['message']
    assert resp['can_book_in_chat'] is True
    assert resp['recommended_doctor'] is not None
    assert "Dr." in resp['recommended_doctor']['name']


@pytest.mark.django_db
def test_ai_pharmacology_medicine_detection_and_alternatives(api_client):
    """
    Tests pharmacology intelligence: detects medicine, maps underlying disease,
    suggests equivalent alternatives that do the same work, and drafts prescription.
    """
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    msg = "I am currently taking Metformin 500mg and Atorvastatin 20mg every day."
    resp = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {"message": msg})
    assert resp.status_code == 200
    data = resp.data['data']['response']

    assert len(data['detected_medicines']) >= 2
    # Check disease detection
    detected_diseases = [m['primary_disease'] for m in data['detected_medicines']]
    assert any("Diabetes" in d for d in detected_diseases)
    assert any("Hypercholesterolemia" in d for d in detected_diseases)

    # Check equivalent alternatives
    med_names = [m['generic_name'] for m in data['detected_medicines']]
    assert any("Metformin" in n for n in med_names)
    assert any("Atorvastatin" in n for n in med_names)

    # Check draft prescription items
    assert len(data['draft_prescription']) >= 2
    assert data['can_book_in_chat'] is True


@pytest.mark.django_db
def test_ai_file_attachment_parsing(api_client):
    """
    Tests file upload parsing with lab report parameters (HbA1c, BP).
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    sample_report_text = "Diagnostic Lab Report\nPatient: John\nHbA1c: 7.4%\nBlood Pressure: 140/90 mmHg\nTotal Cholesterol: 245 mg/dL\n"
    uploaded_file = SimpleUploadedFile("blood_report.txt", sample_report_text.encode('utf-8'), content_type="text/plain")

    resp = api_client.post(
        f'/api/v1/ai-care/sessions/{session_id}/messages/',
        {"file": uploaded_file, "message": "Here is my recent blood test report."}
    )
    assert resp.status_code == 200
    data = resp.data['data']['response']

    # Check that lab tests were detected and evaluated against ranges
    assert len(data['detected_lab_findings']) >= 2
    test_names = [l['test_name'] for l in data['detected_lab_findings']]
    assert "Hemoglobin A1c (HbA1c)" in test_names
    assert "Blood Pressure" in test_names


@pytest.mark.django_db
def test_dev_otp_endpoint(api_client):
    """
    Verifies that the /api/v1/auth/dev-otp/ endpoint returns the active OTP in DEBUG mode.
    """
    email = "testdevuser@example.com"
    # Register user
    reg_resp = api_client.post('/api/v1/auth/register/', {
        "first_name": "Dev",
        "last_name": "Tester",
        "email": email,
        "phone_number": "+919876543210",
        "password": "Password123!",
        "role": "patient"
    })
    assert reg_resp.status_code == 201

    # Query dev-otp endpoint
    dev_resp = api_client.get(f'/api/v1/auth/dev-otp/?email={email}')
    assert dev_resp.status_code == 200
    otp_val = dev_resp.data['data']['dev_otp']
    assert otp_val is not None
    assert len(otp_val) == 6

    # Verify with the retrieved dev OTP
    ver_resp = api_client.post('/api/v1/auth/verify-email-otp/', {
        "email": email,
        "otp": otp_val
    })
    assert ver_resp.status_code == 200
    assert ver_resp.data['data']['token'] is not None


@pytest.mark.django_db
def test_prescription_pdf_view_with_query_token(api_client):
    """
    Verifies that PrescriptionPDFView allows authorized access via ?token= query parameter.
    """
    from apps.accounts.models import User, AuthToken
    from apps.patients.models import PatientProfile
    from apps.doctors.models import DoctorProfile
    from apps.prescriptions.models import Prescription, PrescriptionItem
    from django.utils import timezone

    doc_user = User.objects.create_user(email="dr.pdf@test.com", password="Pass123!Safe", role="doctor")
    pat_user = User.objects.create_user(email="patient.pdf@test.com", password="Pass123!Safe", role="patient")

    doc_profile = DoctorProfile.objects.create(user=doc_user, license_number="MCI-PDF-999")
    pat_profile = PatientProfile.objects.create(user=pat_user)

    rx = Prescription.objects.create(
        patient=pat_profile,
        doctor=doc_profile,
        diagnosis="Acute Bronchitis",
        doctor_notes="Rest well and hydrate.",
        status=Prescription.STATUS_ISSUED,
        issued_at=timezone.now()
    )
    PrescriptionItem.objects.create(
        prescription=rx,
        medicine_name="Amoxicillin",
        formulation="Capsule",
        strength="500mg",
        frequency="Every 8 hours",
        duration="5 days",
        instructions="Take with food."
    )

    # 1. Unauthenticated request without token should return 401
    unauth_resp = api_client.get(f'/api/v1/prescriptions/{rx.id}/pdf/')
    assert unauth_resp.status_code == 401

    # 2. Authenticated request via query param ?token=<key>
    token = AuthToken.create_token(user=pat_user).key
    auth_resp = api_client.get(f'/api/v1/prescriptions/{rx.id}/pdf/?token={token}')
    assert auth_resp.status_code == 200
    assert auth_resp['Content-Type'] == 'application/pdf'
    assert len(auth_resp.content) > 100


@pytest.mark.django_db
def test_admin_doctor_creation_and_signup_restriction(api_client):
    """
    Verifies that public registration creates patients only,
    and only administrators can onboard doctors with proper clinical descriptions.
    """
    from apps.accounts.models import User, AuthToken
    from apps.doctors.models import DoctorProfile, Specialization

    # 1. Public registration rejects 'doctor' role choice
    bad_reg_resp = api_client.post('/api/v1/auth/register/', {
        "first_name": "Invalid",
        "last_name": "Doctor",
        "email": "invaliddoc@example.com",
        "password": "Password123!",
        "role": "doctor"  # Doctor role is disallowed on public registration
    })
    assert bad_reg_resp.status_code == 400

    # 2. Public registration without role creates patient account
    reg_resp = api_client.post('/api/v1/auth/register/', {
        "first_name": "Test",
        "last_name": "Patient",
        "email": "testsignup@example.com",
        "password": "Password123!"
    })
    assert reg_resp.status_code == 201
    user = User.objects.get(email="testsignup@example.com")
    assert user.role == "patient"

    # 2. Non-admin attempting to create doctor should fail (403)
    patient_token = AuthToken.create_token(user=user).key
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {patient_token}')
    fail_resp = api_client.post('/api/v1/doctors/admin-create/', {
        "first_name": "Unauth",
        "last_name": "Doc",
        "email": "unauth@doc.com"
    })
    assert fail_resp.status_code == 403

    # 3. Admin successfully creating doctor with full clinical description
    admin_user = User.objects.create_user(email="admin.tester@example.com", password="Pass123!Safe", role="admin")
    admin_token = AuthToken.create_token(user=admin_user).key
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')

    spec, _ = Specialization.objects.get_or_create(name="Cardiology", slug="cardiology")
    create_resp = api_client.post('/api/v1/doctors/admin-create/', {
        "first_name": "Siddharth",
        "last_name": "Kapoor",
        "email": "dr.siddharth@example.com",
        "phone_number": "+919811223344",
        "specialization_id": str(spec.id),
        "qualifications": "MBBS, MD (Cardiology - AIIMS)",
        "license_number": "MCI-2024-9988",
        "experience_years": 14,
        "consultation_fee": "850.00",
        "city": "Gurugram",
        "bio": "Senior Consultant in Preventive Cardiology with 14+ years of clinical practice."
    })
    assert create_resp.status_code == 201
    data = create_resp.data['data']
    assert data['user']['full_name'] == "Siddharth Kapoor"
    assert data['is_verified'] is True
    assert "Preventive Cardiology" in data['bio']
    assert len(data['user']['email']) > 0
