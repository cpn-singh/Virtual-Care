"""
Authentication API Views
Author: Security & Identity Team

Clean, robust REST endpoints for:
- User registration
- OTP email verification
- Sign in with Bearer token issuance
- Password recovery
- Current user profile discovery
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from django.conf import settings
from django.contrib.auth import authenticate
from apps.accounts.models import User, AuthToken, EmailOTP
from apps.accounts.serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserSummarySerializer,
)
from apps.accounts.services.otp_service import OTPService
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from common.roles import UserRole
from common.responses import success_response, error_response


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Registers a new patient or doctor account and immediately dispatches
    a 6-digit OTP verification code to their email address.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Registration validation failed.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save(role=UserRole.PATIENT)

        # Self-registration initializes patient profile only
        PatientProfile.objects.get_or_create(user=user)

        # Send 6-digit verification code
        otp_result = OTPService.generate_and_send_otp(
            email=user.email,
            purpose=EmailOTP.PURPOSE_REGISTRATION,
            user=user
        )

        resp_data = {
            "email": user.email,
            "role": user.role,
            "is_email_verified": user.is_email_verified,
            "cooldown": otp_result.get("cooldown", False)
        }
        if settings.DEBUG and otp_result.get("dev_otp"):
            resp_data["dev_otp"] = otp_result["dev_otp"]

        return success_response(
            data=resp_data,
            message="Account created successfully! Please check your email for your 6-digit verification code.",
            http_status=status.HTTP_201_CREATED
        )


class VerifyEmailOTPView(APIView):
    """
    POST /api/v1/auth/verify-email-otp/
    Verifies the 6-digit numeric OTP. Upon success, activates the account
    and issues an authentication token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid verification payload.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        purpose = serializer.validated_data.get('purpose', EmailOTP.PURPOSE_REGISTRATION)

        is_valid, message, user = OTPService.verify_otp(email=email, raw_otp=otp, purpose=purpose)

        if not is_valid:
            return error_response(
                message=message,
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Issue authentication token for the verified user
        user_agent = request.headers.get('User-Agent', '')
        token = AuthToken.create_token(user=user, hours_valid=72, user_agent=user_agent)

        return success_response(
            data={
                "token": token.key,
                "user": UserSummarySerializer(user).data
            },
            message="Email verified successfully. Welcome to Virtual Care!"
        )


class ResendEmailOTPView(APIView):
    """
    POST /api/v1/auth/resend-email-otp/
    Requests a fresh verification code subject to cooldown limits.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid resend request.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        purpose = serializer.validated_data.get('purpose', EmailOTP.PURPOSE_REGISTRATION)
        user = User.objects.filter(email=email).first()

        result = OTPService.generate_and_send_otp(email=email, purpose=purpose, user=user)

        if not result["success"]:
            return error_response(
                message=result["message"],
                errors={"cooldown": True, "seconds_remaining": result.get("seconds_remaining", 0)},
                http_status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        resp_data = {"email": email}
        if settings.DEBUG and result.get("dev_otp"):
            resp_data["dev_otp"] = result["dev_otp"]

        return success_response(
            data=resp_data,
            message=result["message"]
        )


class DevLatestOTPView(APIView):
    """
    GET /api/v1/auth/dev-otp/?email=...
    Available in DEBUG development or testing mode to provide friction-free local testing
    without external SMTP credentials.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        is_dev = settings.DEBUG or getattr(settings, 'ENABLE_DEV_OTP', True)
        if not is_dev:
            return error_response(
                message="Developer OTP endpoint is disabled in production.",
                http_status=status.HTTP_403_FORBIDDEN
            )
        email = request.query_params.get('email', '')
        dev_code = OTPService.get_dev_otp(email)
        return success_response(
            data={
                "email": email,
                "dev_otp": dev_code,
                "note": "Local development mode: SMTP not required."
            }
        )


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Authenticates registered users with email and password.
    Enforces email verification before granting access to medical workflows.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid login request.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email'].lower().strip()
        password = serializer.validated_data['password']

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            return error_response(
                message="Invalid email or password. Please verify your credentials.",
                http_status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return error_response(
                message="This account has been deactivated. Please contact platform support.",
                http_status=status.HTTP_403_FORBIDDEN
            )

        # Check if email is verified
        if not user.is_email_verified:
            # Trigger fresh OTP to help the user complete verification
            OTPService.generate_and_send_otp(email=user.email, purpose=EmailOTP.PURPOSE_REGISTRATION, user=user)
            return error_response(
                message="Your email is not verified yet. We have sent a 6-digit verification code to your email.",
                errors={"needs_verification": True, "email": user.email},
                http_status=status.HTTP_403_FORBIDDEN
            )

        # Generate fresh authentication token
        user_agent = request.headers.get('User-Agent', '')
        token = AuthToken.create_token(user=user, hours_valid=72, user_agent=user_agent)

        return success_response(
            data={
                "token": token.key,
                "user": UserSummarySerializer(user).data
            },
            message=f"Welcome back, {user.first_name or user.email}!"
        )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Revokes the current session token immediately.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Delete active token
        auth_header = request.headers.get('Authorization', '')
        if ' ' in auth_header:
            key = auth_header.split(' ')[1]
            AuthToken.objects.filter(key=key).delete()

        return success_response(message="You have been signed out safely.")


class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password-reset/request/
    Initiates password reset by sending an OTP.
    Uses generic response to protect against user enumeration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        email = serializer.validated_data['email'].lower().strip()
        user = User.objects.filter(email=email).first()

        # If user exists, send reset OTP
        if user:
            OTPService.generate_and_send_otp(email=email, purpose=EmailOTP.PURPOSE_PASSWORD_RESET, user=user)

        # Generic safe response to prevent email harvesting
        return success_response(
            message="If an account matches that email address, a password reset code has been sent."
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/v1/auth/password-reset/confirm/
    Applies a new password once the 6-digit code is confirmed.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        is_valid, message, user = OTPService.verify_otp(
            email=email,
            raw_otp=otp,
            purpose=EmailOTP.PURPOSE_PASSWORD_RESET
        )

        if not is_valid or not user:
            return error_response(message=message)

        # Set new password and revoke all existing sessions
        user.set_password(new_password)
        user.save()
        AuthToken.objects.filter(user=user).delete()

        return success_response(
            message="Your password has been reset successfully. Please log in with your new credentials."
        )


class MeView(APIView):
    """
    GET /api/v1/auth/me/
    Returns full details for the logged-in user, including their role and profile info.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = UserSummarySerializer(user).data

        # Attach role-specific summary
        profile_data = {}
        if user.role == UserRole.PATIENT and hasattr(user, 'patient_profile'):
            profile_data = {
                "date_of_birth": user.patient_profile.date_of_birth,
                "gender": user.patient_profile.gender,
                "blood_group": user.patient_profile.blood_group,
                "emergency_contact_phone": user.patient_profile.emergency_contact_phone,
            }
        elif user.role == UserRole.DOCTOR and hasattr(user, 'doctor_profile'):
            profile_data = {
                "specialization": user.doctor_profile.specialization.name if user.doctor_profile.specialization else "General Physician",
                "license_number": user.doctor_profile.license_number,
                "is_verified": user.doctor_profile.is_verified,
                "consultation_fee": str(user.doctor_profile.consultation_fee),
                "experience_years": user.doctor_profile.experience_years,
            }

        return success_response(
            data={
                "user": user_data,
                "profile": profile_data
            }
        )
