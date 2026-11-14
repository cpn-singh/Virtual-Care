"""
WhatsApp Notification Service for Clinicians and Patients
Author: Communication & Clinical Systems Team

Supports:
1. Twilio WhatsApp API
2. Meta (Facebook) WhatsApp Cloud API
3. Simulated/Console Mode (Production-ready logging, DB record, and direct wa.me link generation)
"""

import logging
import urllib.parse
import re
import requests
from django.conf import settings
from django.utils import timezone
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


class WhatsAppService:
    @staticmethod
    def clean_phone_number(phone: str) -> str:
        """
        Cleans and formats phone numbers to standard E.164.
        Defaulting to +91 (India) if 10 digits are provided without a country code.
        """
        if not phone:
            return ""
        
        # Remove whitespace, hyphens, and brackets
        cleaned = re.sub(r'[\s\-\(\)\.]', '', str(phone).strip())
        
        if cleaned.startswith('+'):
            return cleaned
        
        # If starts with 00, convert to +
        if cleaned.startswith('00'):
            return '+' + cleaned[2:]
        
        # 10 digits default to India (+91)
        if len(cleaned) == 10 and cleaned.isdigit():
            return f"+91{cleaned}"
        
        # 12 digits starting with 91
        if len(cleaned) == 12 and cleaned.startswith('91') and cleaned.isdigit():
            return f"+{cleaned}"
            
        return f"+{cleaned}" if cleaned.isdigit() else cleaned

    @classmethod
    def generate_wa_deep_link(cls, phone: str, message: str) -> str:
        """
        Generates a 1-click wa.me URL for instant WhatsApp web / desktop opening.
        """
        clean_phone = cls.clean_phone_number(phone).replace('+', '')
        encoded_text = urllib.parse.quote(message)
        return f"https://wa.me/{clean_phone}?text={encoded_text}"

    @classmethod
    def send_message(cls, to_phone: str, message: str, user=None, notification_type=Notification.TYPE_SYSTEM, metadata=None) -> dict:
        """
        Unified dispatch: sends via configured provider (Twilio, Meta, or Simulated).
        Always logs and persists an in-app audit record in the Notification table.
        """
        if metadata is None:
            metadata = {}

        formatted_phone = cls.clean_phone_number(to_phone)
        wa_link = cls.generate_wa_deep_link(formatted_phone, message) if formatted_phone else ""
        metadata['wa_link'] = wa_link
        metadata['recipient_phone'] = formatted_phone

        provider = getattr(settings, 'WHATSAPP_PROVIDER', 'simulated').lower()
        result = {
            "success": False,
            "provider": provider,
            "recipient": formatted_phone,
            "wa_link": wa_link,
            "status": "pending",
            "message_id": "",
        }

        if not formatted_phone:
            result["status"] = "missing_phone"
            result["error"] = "No phone number available for recipient."
            logger.warning("[WhatsApp] Message not sent: recipient phone is empty.")
            return result

        # 1. TWILIO WHATSAPP DISPATCH
        if provider == 'twilio' and getattr(settings, 'TWILIO_ACCOUNT_SID', None) and getattr(settings, 'TWILIO_AUTH_TOKEN', None):
            try:
                sid = settings.TWILIO_ACCOUNT_SID
                token = settings.TWILIO_AUTH_TOKEN
                from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', '+14155238886')
                if not from_number.startswith('whatsapp:'):
                    from_number = f"whatsapp:{from_number}"
                to_number = f"whatsapp:{formatted_phone}"

                url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
                resp = requests.post(
                    url,
                    auth=(sid, token),
                    data={
                        'From': from_number,
                        'To': to_number,
                        'Body': message,
                    },
                    timeout=10
                )
                if resp.status_code in (200, 201):
                    resp_data = resp.json()
                    result["success"] = True
                    result["status"] = "delivered"
                    result["message_id"] = resp_data.get('sid', '')
                else:
                    result["status"] = "failed"
                    result["error"] = resp.text
                    logger.error(f"[WhatsApp Twilio Error] {resp.status_code}: {resp.text}")
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                logger.exception(f"[WhatsApp Twilio Exception] {e}")

        # 2. META WHATSAPP CLOUD API DISPATCH
        elif provider == 'meta' and getattr(settings, 'WHATSAPP_CLOUD_API_TOKEN', None) and getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None):
            try:
                token = settings.WHATSAPP_CLOUD_API_TOKEN
                phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
                clean_target = formatted_phone.replace('+', '')

                url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": clean_target,
                    "type": "text",
                    "text": {"preview_url": True, "body": message}
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    resp_data = resp.json()
                    result["success"] = True
                    result["status"] = "delivered"
                    result["message_id"] = resp_data.get('messages', [{}])[0].get('id', '')
                else:
                    result["status"] = "failed"
                    result["error"] = resp.text
                    logger.error(f"[WhatsApp Meta Error] {resp.status_code}: {resp.text}")
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                logger.exception(f"[WhatsApp Meta Exception] {e}")

        # 3. SIMULATED / CONSOLE FALLBACK
        else:
            result["success"] = True
            result["status"] = "simulated"
            result["message_id"] = f"sim-{timezone.now().timestamp()}"
            print("\n" + "=" * 65)
            print("📱 [WHATSAPP NOTIFICATION DISPATCH - SIMULATED / CONSOLE]")
            print(f"Recipient: {formatted_phone} {f'({user.full_name})' if user else ''}")
            print(f"Direct WhatsApp Link: {wa_link}")
            print("-" * 65)
            print(message)
            print("=" * 65 + "\n")

        # Persist Notification record for audit and dashboard display
        if user:
            try:
                title = "WhatsApp Notification"
                if notification_type == Notification.TYPE_APPOINTMENT:
                    title = "WhatsApp: New Appointment"
                elif notification_type == Notification.TYPE_VIDEOCALL:
                    title = "WhatsApp: Video Consultation Ready"

                Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    channel=Notification.CHANNEL_BOTH,
                    whatsapp_status=result["status"],
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to record Notification model entry: {e}")

        return result

    @classmethod
    def send_appointment_booked_doctor_alert(cls, appointment) -> dict:
        """
        Sends an automated WhatsApp alert to the attending doctor when a patient books.
        """
        doctor = appointment.doctor
        if not doctor:
            return {"success": False, "error": "No doctor associated with appointment."}

        # Check if doctor has enabled WhatsApp alerts
        if not getattr(doctor, 'whatsapp_notifications_enabled', True):
            logger.info(f"Doctor {doctor.user.email} has disabled WhatsApp notifications.")
            return {"success": False, "status": "disabled", "message": "Doctor disabled WhatsApp notifications."}

        recipient_phone = doctor.effective_whatsapp_number
        if not recipient_phone:
            recipient_phone = getattr(doctor.user, 'phone_number', '')

        patient_name = appointment.patient.user.full_name
        doc_name = doctor.user.full_name
        app_url = getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')

        # Format WhatsApp message with rich markdown
        message = (
            f"🏥 *Virtual Care - New Appointment Alert*\n\n"
            f"Dear Dr. {doc_name},\n"
            f"A new patient consultation has been confirmed on your schedule:\n\n"
            f"👤 *Patient:* {patient_name}\n"
            f"📅 *Date:* {appointment.scheduled_date}\n"
            f"⏰ *Time:* {appointment.scheduled_time}\n"
            f"🩺 *Reason for Visit:* {appointment.reason_for_visit}\n"
        )
        if appointment.patient_symptoms_summary:
            message += f"📝 *Intake Summary:* {appointment.patient_symptoms_summary}\n"
        
        message += (
            f"💰 *Fee:* ₹{appointment.consultation_fee}\n\n"
            f"👉 *Open Doctor Portal:* {app_url}/doctor/dashboard\n\n"
            f"_Virtual Care Telemedicine Clinical Governance_"
        )

        metadata = {
            "appointment_id": str(appointment.id),
            "patient_name": patient_name,
            "scheduled_date": str(appointment.scheduled_date),
            "scheduled_time": str(appointment.scheduled_time),
            "alert_type": "appointment_booked"
        }

        return cls.send_message(
            to_phone=recipient_phone,
            message=message,
            user=doctor.user,
            notification_type=Notification.TYPE_APPOINTMENT,
            metadata=metadata
        )

    @classmethod
    def send_video_call_doctor_alert(cls, appointment, room_url: str = None) -> dict:
        """
        Sends an immediate WhatsApp alert to the attending doctor when the patient
        enters the waiting room or when video consultation starts.
        """
        doctor = appointment.doctor
        if not doctor:
            return {"success": False, "error": "No doctor associated with appointment."}

        if not getattr(doctor, 'whatsapp_notifications_enabled', True):
            return {"success": False, "status": "disabled", "message": "Doctor disabled WhatsApp notifications."}

        recipient_phone = doctor.effective_whatsapp_number
        if not recipient_phone:
            recipient_phone = getattr(doctor.user, 'phone_number', '')

        patient_name = appointment.patient.user.full_name
        doc_name = doctor.user.full_name
        app_url = getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')
        
        # Link to direct video consultation room in the frontend
        if not room_url:
            room_url = f"{app_url}/consultation/{appointment.id}"

        short_id = str(appointment.id)[:8]

        message = (
            f"📹 *Virtual Care - Video Call Starting Now!*\n\n"
            f"Dear Dr. {doc_name},\n"
            f"Your patient *{patient_name}* is ready in the virtual consultation room.\n\n"
            f"🆔 *Appointment ID:* #{short_id}\n"
            f"⏰ *Slot:* {appointment.scheduled_date} at {appointment.scheduled_time}\n"
            f"🩺 *Reason:* {appointment.reason_for_visit}\n\n"
            f"🔗 *Tap to Join Video Call:* \n{room_url}\n\n"
            f"Please enter the room to begin the clinical consultation.\n\n"
            f"_Virtual Care Telehealth Systems_"
        )

        metadata = {
            "appointment_id": str(appointment.id),
            "patient_name": patient_name,
            "room_url": room_url,
            "alert_type": "video_call_ready"
        }

        return cls.send_message(
            to_phone=recipient_phone,
            message=message,
            user=doctor.user,
            notification_type=Notification.TYPE_VIDEOCALL,
            metadata=metadata
        )

    @classmethod
    def send_test_doctor_alert(cls, doctor_profile, test_phone: str = None) -> dict:
        """
        Sends a test WhatsApp message to verify doctor's WhatsApp integration.
        """
        phone = test_phone or doctor_profile.effective_whatsapp_number
        doc_name = doctor_profile.user.full_name
        app_url = getattr(settings, 'FRONTEND_APP_URL', 'http://localhost:3000').rstrip('/')

        message = (
            f"✅ *Virtual Care - WhatsApp Integration Verified!*\n\n"
            f"Hello Dr. {doc_name},\n"
            f"Your WhatsApp notifications for appointment bookings and video calls are successfully active!\n\n"
            f"📱 *Registered Phone:* {phone}\n"
            f"🌐 *Portal URL:* {app_url}/doctor/dashboard\n\n"
            f"You will receive instant alerts here whenever a patient books or joins a video consultation."
        )

        metadata = {
            "alert_type": "test_verification",
            "doctor_id": str(doctor_profile.id)
        }

        return cls.send_message(
            to_phone=phone,
            message=message,
            user=doctor_profile.user,
            notification_type=Notification.TYPE_SYSTEM,
            metadata=metadata
        )
