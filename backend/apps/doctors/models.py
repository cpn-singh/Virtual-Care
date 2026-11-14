"""
Doctor Profile and Clinical Availability Models
Author: Clinical Operations Team

Manages medical qualifications, licensing verification flags,
consultation pricing, and weekly schedule slots.
"""

import uuid
from django.db import models
from django.conf import settings


class Specialization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    icon_name = models.CharField(max_length=50, default='Stethoscope')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors'
    )
    license_number = models.CharField(max_length=100, blank=True, help_text="Medical Council Registration ID")
    qualifications = models.CharField(max_length=255, default='MBBS', help_text="e.g. MBBS, MD, FRCS")
    experience_years = models.PositiveSmallIntegerField(default=5)
    bio = models.TextField(blank=True)
    clinic_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)

    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    # Verification workflow
    is_verified = models.BooleanField(
        default=False,
        help_text="Only verified doctors can conduct appointments and sign digital prescriptions"
    )
    is_available_for_telehealth = models.BooleanField(default=True)

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_consultations = models.PositiveIntegerField(default=0)

    # WhatsApp Notifications configuration
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Doctor WhatsApp phone number with country code, e.g. +919876543210"
    )
    whatsapp_notifications_enabled = models.BooleanField(
        default=True,
        help_text="Send WhatsApp alerts for new appointments and incoming video calls"
    )

    # CareConnect Institutional Email & Working Mailbox
    careconnect_email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Official @careconnect.health institutional email provisioned by AI"
    )
    personal_email = models.EmailField(
        max_length=255,
        blank=True,
        help_text="Doctor's personal/forwarding email address (receives forwarded emails)"
    )
    email_forwarding_enabled = models.BooleanField(
        default=True,
        help_text="Automatically forward CareConnect institutional emails to personal email"
    )
    email_provisioned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when official CareConnect email was provisioned"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def effective_careconnect_email(self) -> str:
        """Returns the doctor's official CareConnect institutional email."""
        if self.careconnect_email and self.careconnect_email.strip():
            return self.careconnect_email.strip()
        if hasattr(self, 'user') and self.user and self.user.email and '@careconnect.' in self.user.email:
            return self.user.email.strip()
        return ''

    @property
    def effective_whatsapp_number(self) -> str:
        """Returns the doctor's dedicated WhatsApp number or falls back to user phone number."""
        if self.whatsapp_number and self.whatsapp_number.strip():
            return self.whatsapp_number.strip()
        if hasattr(self, 'user') and self.user and self.user.phone_number:
            return self.user.phone_number.strip()
        return ''

    class Meta:
        ordering = ['-rating', '-experience_years']

    def __str__(self):
        spec = self.specialization.name if self.specialization else "General Medicine"
        return f"Dr. {self.user.full_name} ({spec}) - Verified: {self.is_verified}"


class DoctorAvailability(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name_plural = 'Doctor availabilities'

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, 'Unknown')
        return f"{self.doctor.user.full_name}: {day_name} {self.start_time}-{self.end_time}"
