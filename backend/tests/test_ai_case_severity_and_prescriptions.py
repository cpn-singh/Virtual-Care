"""
Tests for Clinical Triage Severity Classification & Normal Generic Prescriptions
Author: Clinical Governance & Safety Board
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.doctors.models import DoctorProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def verified_doctor():
    doc_user = User.objects.create_user(
        email="dr.assigned@careconnect.health",
        password="TestPassword2026!",
        first_name="Vikram",
        last_name="Sen",
        role="doctor"
    )
    return DoctorProfile.objects.create(
        user=doc_user,
        license_number="MCI-99221",
        qualifications="MBBS, MD",
        consultation_fee=500.00,
        is_verified=True,
    )


@pytest.mark.django_db
def test_serious_case_assigns_doctor(api_client, verified_doctor):
    """
    Serious clinical case (e.g. severe joint pain 8/10 or chest tightness)
    MUST assign a verified doctor with an in-chat booking card.
    """
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    # Turn 1: Chief Complaint (Severe joint pain)
    t1 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "Severe joint pain and severe swelling in both knees."
    })
    assert t1.status_code == 200

    # Turn 2: Duration
    t2 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "Started 4 days ago and is getting worse."
    })
    assert t2.status_code == 200

    # Turn 3: Severity rating (High pain score 8/10)
    t3 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "Pain rating is 8 out of 10, very severe."
    })
    assert t3.status_code == 200

    # Turn 4: Associated symptoms -> Final Assessment
    t4 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "I also have knee stiffness and difficulty walking."
    })
    assert t4.status_code == 200
    resp = t4.data['data']['response']

    # Must assign a doctor for serious case
    assert resp['can_book_in_chat'] is True
    assert resp['recommended_doctor'] is not None
    assert "Dr." in resp['recommended_doctor']['name']
    assert "Serious" in resp['message']


@pytest.mark.django_db
def test_normal_case_cold_provides_generic_prescription_without_doctor(api_client, verified_doctor):
    """
    Normal/mild routine case (e.g. common cold, mild runny nose, mild throat tickle)
    MUST NOT assign a doctor and instead MUST formulate a normal digital prescription
    with safe generic medicines.
    """
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    # Turn 1: Mild complaint
    t1 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "I have a mild runny nose and slight sneezing since yesterday."
    })
    assert t1.status_code == 200

    # Turn 2: Duration
    t2 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "Just started yesterday morning."
    })
    assert t2.status_code == 200

    # Turn 3: Mild severity
    t3 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "Severity is mild, about 2 out of 10."
    })
    assert t3.status_code == 200

    # Turn 4: No serious history -> Final Assessment
    t4 = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "No fever, no breathlessness, no other problems."
    })
    assert t4.status_code == 200
    resp = t4.data['data']['response']

    # Must NOT force a doctor assignment
    assert resp['can_book_in_chat'] is False
    assert resp['recommended_doctor'] is None

    # Must provide normal generic prescription
    assert "draft_prescription" in resp
    assert len(resp['draft_prescription']) >= 2

    # Verify generic medicines include Paracetamol and Cetirizine
    med_names = [item['medicine_name'] for item in resp['draft_prescription']]
    assert any("Cetirizine" in name for name in med_names)
    assert any("Paracetamol" in name for name in med_names)

    # Message explains generic savings and self-care
    assert "Generic Medicine" in resp['message']
    assert "Not Required" in resp['message'] or "not required" in resp['message']


@pytest.mark.django_db
def test_direct_prescription_request_for_acidity(api_client, verified_doctor):
    """
    Direct user query requesting medicine for routine acidity returns
    generic prescription (Pantoprazole / Antacid) without assigning a doctor.
    """
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    resp = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "I have mild acidity and stomach gas, please suggest medicine for this."
    })
    assert resp.status_code == 200
    data = resp.data['data']['response']

    assert data['can_book_in_chat'] is False
    assert data['recommended_doctor'] is None
    assert len(data['draft_prescription']) >= 1

    med_names = [m['medicine_name'] for m in data['draft_prescription']]
    assert any("Pantoprazole" in name for name in med_names)
    assert "Generic" in data['message']


@pytest.mark.django_db
def test_direct_prescription_request_for_serious_symptoms_assigns_doctor(api_client, verified_doctor):
    """
    Direct user query requesting medicine for a SERIOUS case (e.g. chest pain)
    MUST assign a doctor rather than just dispensing routine pills.
    """
    init_resp = api_client.post('/api/v1/ai-care/sessions/')
    session_id = init_resp.data['data']['id']

    resp = api_client.post(f'/api/v1/ai-care/sessions/{session_id}/messages/', {
        "message": "I have severe chest tightness and left arm numbness, please give me medicine for this."
    })
    assert resp.status_code == 200
    data = resp.data['data']['response']

    # Must assign doctor or trigger red-flag emergency escalation
    assert data.get('can_book_in_chat') is True or data.get('emergency_action_required') is True
