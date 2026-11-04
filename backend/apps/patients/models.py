"""
Patient Profile Models
Author: Clinical Systems Engineering Team

Stores personal health metrics, allergy declarations, emergency contacts,
and explicit user consent settings.
"""

import uuid
from django.db import models
from django.conf import settings


class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='prefer_not_to_say')
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, default='unknown')
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Health context
    allergies = models.TextField(blank=True, help_text="Known drug, food, or environmental allergies")
    chronic_conditions = models.TextField(blank=True, help_text="e.g. Asthma, Hypertension, Diabetes")
    current_medications = models.TextField(blank=True, help_text="List of active medications")

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    # Privacy & AI Consent
    consent_ai_triage = models.BooleanField(
        default=True,
        help_text="Explicit consent to gather symptom intake with the AI Care Assistant"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Patient: {self.user.full_name} ({self.user.email})"
