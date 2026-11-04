"""
OTP Generation & Verification Service
Author: Security & Identity Team

Implements secure one-time passwords for email verification and password resets:
- 6-digit cryptographically secure random values
- SHA-256 one-way hashing before database storage
- 60-second resend cooldown to prevent email bombing
- Maximum 5 attempts before invalidation to stop brute-forcing
- Short expiry window (default 10 minutes)
"""

import hashlib
import secrets
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from apps.accounts.models import EmailOTP, User

# In-memory dictionary to hold raw OTPs for local development when SMTP is not configured
_DEV_ACTIVE_OTPS: dict[str, str] = {}


def _hash_otp(raw_otp: str) -> str:
    """Return SHA-256 digest of raw numeric OTP."""
    return hashlib.sha256(raw_otp.strip().encode('utf-8')).hexdigest()


class OTPService:
    @staticmethod
    def get_dev_otp(email: str) -> str | None:
        """Retrieve recent unverified OTP in local development or test mode."""
        return _DEV_ACTIVE_OTPS.get(email.lower().strip())

    @staticmethod
    def generate_and_send_otp(email: str, purpose: str = EmailOTP.PURPOSE_REGISTRATION, user: User = None) -> dict:
        """
        Creates a new 6-digit OTP, saves the hash, and dispatches the email.
        Enforces a cooldown period between resend requests.
        """
        email = email.lower().strip()
        now = timezone.now()

        # Check for active cooldown (e.g. 60 seconds)
        recent_otp = EmailOTP.objects.filter(
            email=email,
            purpose=purpose,
            is_used=False,
            created_at__gte=now - timedelta(seconds=settings.OTP_RESEND_COOLDOWN_SECONDS)
        ).first()

        if recent_otp:
            time_remaining = settings.OTP_RESEND_COOLDOWN_SECONDS - int((now - recent_otp.created_at).total_seconds())
            return {
                "success": False,
                "cooldown": True,
                "seconds_remaining": max(0, time_remaining),
                "message": f"Please wait {time_remaining} seconds before requesting another code."
            }

        # Invalidate any older unused codes for this email and purpose
        EmailOTP.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)

        # Generate a secure 6-digit integer
        raw_otp = f"{secrets.randbelow(900000) + 100000}"
        otp_hash = _hash_otp(raw_otp)

        expiry = now + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        EmailOTP.objects.create(
            user=user,
            email=email,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=expiry
        )

        # Send notification email
        subject_map = {
            EmailOTP.PURPOSE_REGISTRATION: "Verify your Virtual Care account",
            EmailOTP.PURPOSE_LOGIN: "Your login verification code",
            EmailOTP.PURPOSE_PASSWORD_RESET: "Password reset verification code",
        }
        subject = subject_map.get(purpose, "Your verification code")

        message = (
            f"Hello,\n\n"
            f"Your verification code for Virtual Care Telemedicine is:\n\n"
            f"    {raw_otp}\n\n"
            f"This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
            f"If you did not make this request, you can safely ignore this email.\n\n"
            f"Warm regards,\n"
            f"The Virtual Care Healthcare Team"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False
            )
        except Exception as e:
            # When developing locally, console backend prints to terminal; log errors if mail fails
            print(f"[Email Delivery Notice] Failed to send email to {email}: {e}")

        # In development or test mode, store in memory and print notice
        is_dev = settings.DEBUG or getattr(settings, 'ENABLE_DEV_OTP', True)
        dev_otp_value = None
        if is_dev:
            _DEV_ACTIVE_OTPS[email] = raw_otp
            dev_otp_value = raw_otp
            print(f"\n==========================================")
            print(f" [DEV OTP CODE] For: {email} | Purpose: {purpose}")
            print(f" OTP: >>> {raw_otp} <<<")
            print(f"==========================================\n")

        return {
            "success": True,
            "cooldown": False,
            "message": "Verification code has been sent to your email address.",
            "dev_otp": dev_otp_value
        }

    @staticmethod
    def verify_otp(email: str, raw_otp: str, purpose: str = EmailOTP.PURPOSE_REGISTRATION) -> tuple[bool, str, User]:
        """
        Validates the provided OTP.
        Returns: (is_valid: bool, error_message: str, user: User)
        """
        email = email.lower().strip()
        now = timezone.now()

        otp_record = EmailOTP.objects.filter(
            email=email,
            purpose=purpose,
            is_used=False
        ).order_by('-created_at').first()

        if not otp_record:
            return False, "No active verification code found. Please request a new one.", None

        if otp_record.is_expired():
            otp_record.is_used = True
            otp_record.save(update_fields=['is_used'])
            return False, "This verification code has expired. Please request a new one.", None

        if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
            otp_record.is_used = True
            otp_record.save(update_fields=['is_used'])
            return False, "Too many incorrect attempts. This code is now invalid. Please request a new one.", None

        # Verify hash
        expected_hash = _hash_otp(raw_otp)
        if not secrets.compare_digest(otp_record.otp_hash, expected_hash):
            otp_record.attempts += 1
            otp_record.save(update_fields=['attempts'])
            remaining = settings.OTP_MAX_ATTEMPTS - otp_record.attempts
            return False, f"Incorrect code. You have {remaining} attempt(s) remaining.", None

        # Mark OTP as successfully used
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])
        _DEV_ACTIVE_OTPS.pop(email, None)

        # Fetch or link user
        user = otp_record.user or User.objects.filter(email=email).first()
        if user and purpose == EmailOTP.PURPOSE_REGISTRATION:
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])

        return True, "Verification successful.", user
