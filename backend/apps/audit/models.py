"""
Audit Trail Models
Author: Compliance & Information Security Team

Maintains an immutable record of security and clinical events
(prescription issuance, medical record view, login attempt, role elevation).
"""

import uuid
from django.db import models
from django.conf import settings


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events'
    )
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=60, db_index=True)
    resource_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.email if self.actor else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {actor_name} -> {self.action} on {self.resource_type}:{self.resource_id}"
