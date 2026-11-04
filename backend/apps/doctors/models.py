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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
