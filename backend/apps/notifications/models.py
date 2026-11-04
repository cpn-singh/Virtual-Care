"""
Notification Models
Author: Communication Systems Team
"""

import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_APPOINTMENT = 'appointment'
    TYPE_PRESCRIPTION = 'prescription'
    TYPE_PAYMENT = 'payment'
    TYPE_EMERGENCY = 'emergency'
    TYPE_SYSTEM = 'system'

    TYPE_CHOICES = [
        (TYPE_APPOINTMENT, 'Appointment Update'),
        (TYPE_PRESCRIPTION, 'New Prescription'),
        (TYPE_PAYMENT, 'Payment Receipt'),
        (TYPE_EMERGENCY, 'Emergency Alert'),
        (TYPE_SYSTEM, 'System Notice'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_SYSTEM)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"
