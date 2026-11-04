"""
Digital Prescription Models
Author: Clinical Pharmacy & Governance Team

Clinician-issued, tamper-evident prescriptions with full audit trail.
Rules:
- Patients can never edit or finalize prescriptions.
- Issued prescriptions are legally final; updates require an amended version.
"""

import uuid
from django.db import models
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.consultations.models import Consultation
from apps.appointments.models import Appointment


class Prescription(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_ISSUED = 'issued'
    STATUS_AMENDED = 'amended'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ISSUED, 'Issued & Signed'),
        (STATUS_AMENDED, 'Amended'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='prescriptions')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    diagnosis = models.TextField(help_text="Clinical diagnosis formulated by the doctor")
    doctor_notes = models.TextField(blank=True, help_text="Dietary advice, warning signs, follow-up instructions")
    
    version = models.PositiveSmallIntegerField(default=1)
    issued_at = models.DateTimeField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='prescriptions/private/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription {self.id} for {self.patient.user.full_name} by Dr. {self.doctor.user.full_name} ({self.status})"


class PrescriptionItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    
    medicine_name = models.CharField(max_length=200, help_text="Generic / Brand name")
    formulation = models.CharField(max_length=50, default='Tablet', help_text="e.g. Tablet, Capsule, Syrup, Inhaler")
    strength = models.CharField(max_length=50, default='500mg', help_text="e.g. 500mg, 10ml, 5mg/5ml")
    dose = models.CharField(max_length=50, default='1 tablet', help_text="e.g. 1 tablet, 2 puffs")
    frequency = models.CharField(max_length=100, default='Twice daily after meals')
    duration = models.CharField(max_length=50, default='5 days')
    instructions = models.CharField(max_length=255, blank=True, help_text="e.g. Take with warm water, avoid dairy")

    def __str__(self):
        return f"{self.medicine_name} {self.strength} - {self.frequency} for {self.duration}"
