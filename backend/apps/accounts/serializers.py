"""
Authentication Serializers
Author: Security & Identity Team

Validates incoming authentication payloads cleanly and returns helpful error messages.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import User, EmailOTP
from common.roles import UserRole


class UserSummarySerializer(serializers.ModelSerializer):
    """Safe, public-facing user representation."""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone_number',
            'role',
            'is_email_verified',
            'date_joined',
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates user registration input.
    Public registration is strictly restricted to Patients.
    Doctors must be provisioned and credentialed directly by Platform Administrators.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[UserRole.PATIENT],
        default=UserRole.PATIENT,
        required=False
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password', 'role']

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email=normalized).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class VerifyOTPSerializer(serializers.Serializer):
    """Validates 6-digit OTP submission."""
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(
        choices=[EmailOTP.PURPOSE_REGISTRATION, EmailOTP.PURPOSE_LOGIN, EmailOTP.PURPOSE_PASSWORD_RESET],
        default=EmailOTP.PURPOSE_REGISTRATION
    )


class ResendOTPSerializer(serializers.Serializer):
    """Payload to request another verification email."""
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(
        choices=[EmailOTP.PURPOSE_REGISTRATION, EmailOTP.PURPOSE_LOGIN, EmailOTP.PURPOSE_PASSWORD_RESET],
        default=EmailOTP.PURPOSE_REGISTRATION
    )


class LoginSerializer(serializers.Serializer):
    """Validates email + password login credentials."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Requests a password reset code sent to email."""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Applies new password after OTP verification."""
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value
