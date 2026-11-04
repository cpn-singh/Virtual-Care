"""
Consultation & Clinical Notes Models
Author: Telehealth Video & Media Team

Manages secure video room sessions and clinician-authored clinical notes.
"""

import uuid
from django.db import models
from apps.appointments.models import Appointment
from apps.doctors.models import DoctorProfile


class Consultation(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_DISCONNECTED = 'disconnected'

    STATUS_CHOICES = [
        (STATUS_WAITING, 'Waiting Room'),
        (STATUS_ACTIVE, 'Active Call'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_DISCONNECTED, 'Disconnected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='consultation')
    room_id = models.CharField(max_length=120, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
    
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Consultation for Appointment {self.appointment.id} ({self.status})"


class ClinicalNote(models.Model):
    """
    Clinician-entered consultation notes.
    Protected under healthcare privacy standards.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='clinical_note')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='clinical_notes')
    
    chief_complaint = models.TextField(blank=True)
    clinical_observations = models.TextField(blank=True)
    diagnosis_summary = models.TextField(help_text="Clinician's professional clinical diagnosis")
    treatment_advice = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Clinical Note by Dr. {self.doctor.user.full_name} for Consultation {self.consultation.id}"
