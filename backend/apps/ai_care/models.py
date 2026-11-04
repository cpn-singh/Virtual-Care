"""
AI Care Conversation Models
Author: Clinical Safety & AI Governance Team

Maintains patient chat sessions, safety classifications, and clinician handoff summaries.
"""

import uuid
from django.db import models
from django.conf import settings
from apps.patients.models import PatientProfile


class AIConversation(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_ESCALATED = 'escalated_emergency'
    STATUS_HANDED_OFF = 'handed_off_to_doctor'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active Triage Session'),
        (STATUS_ESCALATED, 'Escalated to Emergency Services'),
        (STATUS_HANDED_OFF, 'Handed Off to Clinician'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    session_token = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=200, default='Symptom Care Guidance')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    is_emergency = models.BooleanField(default=False)
    protocol_version = models.CharField(max_length=50, default='1.0.4-CLINICAL')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user_label = self.user.email if self.user else f"Anonymous ({self.session_token[:8]})"
        return f"AI Chat {self.id}: {user_label} - Status: {self.status}"


class AIMessage(models.Model):
    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_SYSTEM = 'system'

    ROLE_CHOICES = [
        (ROLE_USER, 'Patient'),
        (ROLE_ASSISTANT, 'Care Assistant'),
        (ROLE_SYSTEM, 'Safety System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    # Safety metadata
    category = models.CharField(max_length=50, default='routine_care_navigation')
    urgency = models.CharField(max_length=20, default='routine')
    emergency_action_required = models.BooleanField(default=False)
    recommended_next_step = models.CharField(max_length=100, default='offer_doctor_appointment')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role.capitalize()}: {self.content[:40]}..."


class AIHandoff(models.Model):
    """
    Intake summary ready to attach to an appointment for human clinician review.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.OneToOneField(AIConversation, on_delete=models.CASCADE, related_name='handoff')
    patient = models.ForeignKey(PatientProfile, on_delete=models.SET_NULL, null=True, blank=True)
    symptom_summary = models.TextField(help_text="Structured patient-reported symptom intake")
    recommended_specialization = models.CharField(max_length=100, default='General Physician')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Handoff summary for Conversation {self.conversation.id}"
