"""
User and Authentication Models
Author: Security & Identity Team

We use a clean, UUID-based custom user model with strict role isolation:
- Patients
- Doctors
- Administrators

We also maintain one-time password records (EmailOTP) with cryptographically
hashed values, ensuring raw OTPs are never stored in the database.
"""

import uuid
import secrets
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from common.roles import UserRole


class UserManager(BaseUserManager):
    """Custom manager that uses email as the unique identifier for auth."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required to register.")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', UserRole.PATIENT)

        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Primary user model representing Patients, Doctors, and Platform Admins.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PATIENT,
        db_index=True,
        help_text="Primary platform role determining access permissions"
    )

    is_email_verified = models.BooleanField(
        default=False,
        help_text="True if user has validated their email with a 6-digit OTP"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class EmailOTP(models.Model):
    """
    Stores short-lived, single-use One Time Passwords for email verification.
    Security rules:
    - Never store raw OTPs: store SHA-256 hash.
    - Max attempts tracked to prevent brute-force guessing.
    - Explicit expiry and used flags.
    """
    PURPOSE_REGISTRATION = 'registration'
    PURPOSE_LOGIN = 'login'
    PURPOSE_PASSWORD_RESET = 'password_reset'

    PURPOSE_CHOICES = [
        (PURPOSE_REGISTRATION, 'Registration Verification'),
        (PURPOSE_LOGIN, 'Two-Factor Login'),
        (PURPOSE_PASSWORD_RESET, 'Password Reset'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps', null=True, blank=True)
    email = models.EmailField(db_index=True)
    otp_hash = models.CharField(max_length=64, help_text="SHA-256 hash of the 6-digit numeric OTP")
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES, default=PURPOSE_REGISTRATION)
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email} [{self.purpose}] - Used: {self.is_used}"


class AuthToken(models.Model):
    """
    Lightweight, high-performance API token model.
    Allows easy logout, multi-device tracking, and expiration enforcement.
    """
    key = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField(auto_now=True)
    user_agent = models.CharField(max_length=255, blank=True)

    @classmethod
    def create_token(cls, user, hours_valid=48, user_agent=""):
        """Generate a cryptographically secure 40-byte hex key."""
        token_key = secrets.token_hex(32)
        expiry = timezone.now() + timedelta(hours=hours_valid)
        return cls.objects.create(
            key=token_key,
            user=user,
            expires_at=expiry,
            user_agent=user_agent[:255]
        )

    def is_valid(self):
        return timezone.now() < self.expires_at

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Token for {self.user.email} (expires {self.expires_at.strftime('%Y-%m-%d %H:%M')})"
