"""
Doctor AI Email Provisioning & CareConnect Mailbox Service
Author: Platform Clinical Operations & Identity Systems

Automatically synthesizes, validates, provisions, and routes working
official institutional emails for all medical doctors on the CareConnect domain.
"""

import re
import logging
import unicodedata
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from apps.accounts.models import User

logger = logging.getLogger(__name__)


class DoctorAIEmailService:
    DEFAULT_DOMAIN = "careconnect.health"

    @classmethod
    def get_domain(cls, custom_domain: str = None) -> str:
        """Returns the active CareConnect email domain."""
        if custom_domain and custom_domain.strip():
            return custom_domain.strip().lower().lstrip('@')
        return getattr(settings, 'CARECONNECT_EMAIL_DOMAIN', cls.DEFAULT_DOMAIN).lower().lstrip('@')

    @classmethod
    def normalize_name_token(cls, token: str) -> str:
        """Cleans and standardizes names into clean email-safe ASCII handles."""
        if not token:
            return ""

        # Strip Dr / Dr. / Doctor prefixes
        cleaned = re.sub(r'^(dr\.|dr|doctor)\s+', '', token.strip(), flags=re.IGNORECASE)
        
        # Remove accents and normalize unicode
        normalized = unicodedata.normalize('NFKD', cleaned).encode('ASCII', 'ignore').decode('utf-8')
        
        # Keep only alphanumeric characters
        safe = re.sub(r'[^a-zA-Z0-9]', '', normalized).lower()
        return safe

    @classmethod
    def generate_careconnect_email(
        cls,
        first_name: str,
        last_name: str,
        specialization_name: str = "",
        domain: str = None,
        exclude_user_id=None
    ) -> dict:
        """
        AI algorithm that generates candidate CareConnect email handles,
        evaluates uniqueness against User accounts and DoctorProfiles,
        and returns the best collision-free working email address along with alternatives.
        """
        active_domain = cls.get_domain(domain)
        clean_first = cls.normalize_name_token(first_name) or "doctor"
        clean_last = cls.normalize_name_token(last_name) or "care"
        first_initial = clean_first[0] if clean_first else "d"

        clean_spec = ""
        if specialization_name:
            clean_spec = cls.normalize_name_token(specialization_name.split()[0])

        # Candidate heuristics in priority order
        candidates = [
            f"dr.{clean_first}.{clean_last}@{active_domain}",
            f"{clean_first}.{clean_last}@{active_domain}",
            f"dr.{first_initial}.{clean_last}@{active_domain}",
            f"dr.{clean_first}{clean_last}@{active_domain}",
        ]

        if clean_spec:
            candidates.append(f"dr.{clean_first}.{clean_last}.{clean_spec}@{active_domain}")

        def is_email_available(email_candidate: str) -> bool:
            from apps.doctors.models import DoctorProfile
            user_qs = User.objects.filter(email__iexact=email_candidate)
            doc_qs = DoctorProfile.objects.filter(careconnect_email__iexact=email_candidate)
            if exclude_user_id:
                user_qs = user_qs.exclude(id=exclude_user_id)
                doc_qs = doc_qs.exclude(user__id=exclude_user_id)
            return not (user_qs.exists() or doc_qs.exists())

        # Select first available candidate
        selected_email = None
        for cand in candidates:
            if is_email_available(cand):
                selected_email = cand
                break

        # If all standard candidates collided, intelligently append incremental counter
        if not selected_email:
            counter = 2
            while True:
                numbered_cand = f"dr.{clean_first}.{clean_last}{counter}@{active_domain}"
                if is_email_available(numbered_cand):
                    selected_email = numbered_cand
                    break
                counter += 1

        alternatives = [c for c in candidates if c != selected_email and is_email_available(c)][:3]

        return {
            "primary_email": selected_email,
            "handle": selected_email.split('@')[0],
            "domain": active_domain,
            "alternatives": alternatives,
        }

    @classmethod
    def provision_doctor_mailbox(
        cls,
        doctor_profile,
        careconnect_email: str = None,
        personal_email: str = None,
        default_password: str = None,
        send_welcome_alert: bool = True
    ) -> dict:
        """
        Provisions a working official CareConnect institutional email for a doctor,
        sets up forwarding to their personal email, and dispatches a credential/welcome alert.
        """
        user = doctor_profile.user
        spec_name = doctor_profile.specialization.name if doctor_profile.specialization else ""

        # Auto-generate if not explicitly provided
        if not careconnect_email:
            gen_result = cls.generate_careconnect_email(
                first_name=user.first_name,
                last_name=user.last_name,
                specialization_name=spec_name,
                exclude_user_id=user.id
            )
            careconnect_email = gen_result["primary_email"]
        else:
            careconnect_email = careconnect_email.lower().strip()

        # Determine personal / forwarding address
        if not personal_email:
            if user.email and not user.email.lower().endswith(f"@{cls.get_domain()}"):
                personal_email = user.email.lower().strip()
            else:
                personal_email = doctor_profile.personal_email or user.email

        # If user account is currently registered with personal email, switch login email to CareConnect
        # or preserve CareConnect email as primary institutional identity
        old_user_email = user.email
        if not user.email.lower().endswith(f"@{cls.get_domain()}"):
            user.email = careconnect_email
            user.save(update_fields=['email'])

        doctor_profile.careconnect_email = careconnect_email
        doctor_profile.personal_email = personal_email
        doctor_profile.email_forwarding_enabled = True
        doctor_profile.email_provisioned_at = timezone.now()
        doctor_profile.save(update_fields=[
            'careconnect_email',
            'personal_email',
            'email_forwarding_enabled',
            'email_provisioned_at'
        ])

        result = {
            "success": True,
            "doctor_id": str(doctor_profile.id),
            "doctor_name": user.full_name,
            "careconnect_email": careconnect_email,
            "personal_forwarding_email": personal_email,
            "status": "active_and_forwarding",
            "provisioned_at": doctor_profile.email_provisioned_at.isoformat(),
        }

        # Dispatch Welcome & Credential Activation
        if send_welcome_alert:
            cls._send_onboarding_notification(
                doctor_profile=doctor_profile,
                careconnect_email=careconnect_email,
                personal_email=personal_email,
                password=default_password
            )

        return result

    @classmethod
    def _send_onboarding_notification(cls, doctor_profile, careconnect_email: str, personal_email: str, password: str = None):
        """Sends official CareConnect mailbox activation alert via Email and WhatsApp."""
        doc_name = doctor_profile.user.full_name
        app_url = getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')

        subject = f"Welcome to CareConnect - Your Official Institutional Email: {careconnect_email}"
        email_body = (
            f"Dear Dr. {doc_name},\n\n"
            f"Welcome to the CareConnect Telemedicine Medical Staff!\n\n"
            f"Your official working institutional email has been provisioned and activated:\n"
            f"📧 Official Email: {careconnect_email}\n"
            f"🌐 Portal Login: {app_url}/login\n"
        )
        if password:
            email_body += f"🔑 Temporary Password: {password}\n"

        email_body += (
            f"\n📥 Smart Forwarding Active: Any patient appointment notices or clinical communications "
            f"sent to {careconnect_email} will automatically deliver to your personal inbox ({personal_email}).\n\n"
            f"Best regards,\n"
            f"CareConnect Medical Operations & Clinical Governance Team"
        )

        # 1. Send via Django email (console or SMTP)
        try:
            target_inbox = personal_email or careconnect_email
            send_mail(
                subject=subject,
                message=email_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@careconnect.local'),
                recipient_list=[target_inbox],
                fail_silently=True
            )
        except Exception as e:
            logger.warning(f"Could not dispatch onboarding email to {personal_email}: {e}")

        # 2. Send via WhatsApp if available
        try:
            from apps.notifications.services.whatsapp_service import WhatsAppService
            phone = doctor_profile.effective_whatsapp_number
            if phone:
                wa_msg = (
                    f"🏥 *CareConnect - Official Institutional Email Created*\n\n"
                    f"Dear Dr. {doc_name},\n"
                    f"Your verified CareConnect doctor email is now active:\n"
                    f"📧 *{careconnect_email}*\n\n"
                    f"You can now use this email to log into the Clinical Portal.\n"
                    f"👉 *Login:* {app_url}/login\n\n"
                    f"_CareConnect Healthcare Network_"
                )
                WhatsAppService.send_message(
                    to_phone=phone,
                    message=wa_msg,
                    user=doctor_profile.user
                )
        except Exception as e:
            logger.warning(f"Could not dispatch WhatsApp onboarding alert: {e}")

    @classmethod
    def forward_careconnect_email(cls, to_careconnect_email: str, subject: str, message: str) -> bool:
        """
        Working email forwarder: routes incoming emails addressed to a CareConnect doctor
        to their actual personal email address.
        """
        from apps.doctors.models import DoctorProfile
        doc = DoctorProfile.objects.filter(
            careconnect_email__iexact=to_careconnect_email
        ).select_related('user').first()

        if not doc or not doc.personal_email or not doc.email_forwarding_enabled:
            return False

        forward_subject = f"[CareConnect Mailbox] {subject}"
        forward_body = (
            f"--- Forwarded message from your official CareConnect mailbox ({to_careconnect_email}) ---\n\n"
            f"{message}"
        )

        try:
            send_mail(
                subject=forward_subject,
                message=forward_body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@careconnect.local'),
                recipient_list=[doc.personal_email],
                fail_silently=False
            )
            return True
        except Exception as e:
            logger.error(f"Failed to forward CareConnect email to {doc.personal_email}: {e}")
            return False

    @classmethod
    def auto_provision_all_existing_doctors(cls) -> list:
        """
        Provisions CareConnect working emails for all doctors currently in the database.
        """
        from apps.doctors.models import DoctorProfile
        doctors = DoctorProfile.objects.select_related('user', 'specialization').all()
        results = []

        for doc in doctors:
            if not doc.careconnect_email:
                res = cls.provision_doctor_mailbox(doc)
                results.append(res)
            else:
                results.append({
                    "doctor_name": doc.user.full_name,
                    "careconnect_email": doc.careconnect_email,
                    "status": "already_provisioned"
                })

        return results
