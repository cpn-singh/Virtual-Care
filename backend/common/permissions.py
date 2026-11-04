"""
Object-Level & Role-Based Permissions
Author: Security & Identity Team

Never trust the client to hide buttons: always verify authorization at the API layer!
"""

from rest_framework import permissions
from common.roles import UserRole


class IsEmailVerified(permissions.BasePermission):
    """Allows access only to users who have verified their email OTP."""
    message = "Please verify your email address to access this resource."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_email_verified)


class IsPatient(permissions.BasePermission):
    """Allows access only to authenticated patients."""
    message = "This portal is reserved for registered patients."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.PATIENT
        )


class IsDoctor(permissions.BasePermission):
    """Allows access to doctor accounts."""
    message = "This action requires a doctor account."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.DOCTOR
        )


class IsVerifiedDoctor(permissions.BasePermission):
    """Allows access only to clinical doctors whose license has been verified by platform admin."""
    message = "Your medical credentials are currently pending administrative verification."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.role == UserRole.DOCTOR):
            return False
        # Check doctor profile verification flag
        profile = getattr(request.user, 'doctor_profile', None)
        return bool(profile and profile.is_verified)


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access to administrative staff."""
    message = "Administrative privileges required."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == UserRole.ADMIN or request.user.is_staff or request.user.is_superuser)
        )
