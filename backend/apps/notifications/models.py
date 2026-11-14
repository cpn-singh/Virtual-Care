"""
Notification Models
Author: Communication Systems Team
"""

import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_APPOINTMENT = 'appointment'
    TYPE_VIDEOCALL = 'videocall'
    TYPE_PRESCRIPTION = 'prescription'
    TYPE_PAYMENT = 'payment'
    TYPE_EMERGENCY = 'emergency'
    TYPE_SYSTEM = 'system'

    TYPE_CHOICES = [
        (TYPE_APPOINTMENT, 'Appointment Update'),
        (TYPE_VIDEOCALL, 'Video Call Alert'),
        (TYPE_PRESCRIPTION, 'New Prescription'),
        (TYPE_PAYMENT, 'Payment Receipt'),
        (TYPE_EMERGENCY, 'Emergency Alert'),
        (TYPE_SYSTEM, 'System Notice'),
    ]

    CHANNEL_IN_APP = 'in_app'
    CHANNEL_WHATSAPP = 'whatsapp'
    CHANNEL_BOTH = 'both'
    CHANNEL_CHOICES = [
        (CHANNEL_IN_APP, 'In-App'),
        (CHANNEL_WHATSAPP, 'WhatsApp'),
        (CHANNEL_BOTH, 'Both (In-App & WhatsApp)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default=CHANNEL_IN_APP)
    whatsapp_status = models.CharField(max_length=30, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"
