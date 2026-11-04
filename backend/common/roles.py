"""
Role Definitions for Platform Users
Author: Security & Identity Team

We keep user roles clear and strongly typed to prevent privilege escalation.
"""

from django.db import models


class UserRole(models.TextChoices):
    PATIENT = 'patient', 'Patient'
    DOCTOR = 'doctor', 'Doctor'
    ADMIN = 'admin', 'Administrator'
