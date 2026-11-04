"""
Hospital & Emergency Facility Models
Author: Emergency Response Infrastructure Team

Maintains verified physical hospital directories with 24/7 emergency departments,
trauma centers, and direct contact numbers.
"""

import uuid
from django.db import models


class Hospital(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    phone_number = models.CharField(max_length=25)
    emergency_phone = models.CharField(max_length=25, default="112")
    
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    has_emergency_room = models.BooleanField(default=True)
    has_trauma_center = models.BooleanField(default=True)
    has_icu = models.BooleanField(default=True)
    is_24_7 = models.BooleanField(default=True)

    website = models.URLField(blank=True)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name} - {self.city} (ER: {self.has_emergency_room})"
