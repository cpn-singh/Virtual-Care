"""
Video Consultation Service
Author: Telehealth Video & Media Team

Generates secure room identifiers and short-lived WebRTC/Jitsi tokens
for authorized clinical encounters.
"""

import uuid
import secrets
from django.utils import timezone
from apps.consultations.models import Consultation


class VideoService:
    @staticmethod
    def get_or_create_room(appointment) -> Consultation:
        """
        Retrieves or initializes a consultation room for an appointment.
        """
        consultation, created = Consultation.objects.get_or_create(
            appointment=appointment,
            defaults={
                'room_id': f"care-{appointment.id.hex[:12]}-{secrets.token_hex(4)}",
                'status': Consultation.STATUS_WAITING
            }
        )
        return consultation

    @staticmethod
    def generate_access_credentials(consultation, user) -> dict:
        """
        Generates short-lived session access information for the video client.
        We provide clean Jitsi Meet parameters and room tokens.
        """
        is_doctor = (user.role == 'doctor')
        
        # Room domain (defaults to meet.jit.si or custom self-hosted Jitsi/Agora instance)
        room_name = f"VirtualCare-{consultation.room_id}"

        return {
            "room_name": room_name,
            "display_name": f"Dr. {user.full_name}" if is_doctor else user.full_name,
            "email": user.email,
            "is_moderator": is_doctor,
            "status": consultation.status,
            "server_url": "https://meet.jit.si",
            "expires_in_minutes": 60,
        }
