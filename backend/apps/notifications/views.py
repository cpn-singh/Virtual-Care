"""
Notifications API Views
Author: Communication Systems Team
"""

from rest_framework.views import APIView
from rest_framework import permissions, serializers
from apps.notifications.models import Notification
from apps.notifications.services.whatsapp_service import WhatsAppService
from common.responses import success_response


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'channel',
            'whatsapp_status',
            'metadata',
            'is_read',
            'created_at',
        ]


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:30]
        return success_response(data=NotificationSerializer(notifs, many=True).data)

    def post(self, request):
        """Mark all notifications as read."""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read.")


class WhatsAppTestView(APIView):
    """
    POST /api/v1/notifications/whatsapp/test/
    Sends a test WhatsApp notification to the doctor's phone or provided number.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        phone = request.data.get('phone_number')
        user = request.user
        
        doctor_profile = getattr(user, 'doctor_profile', None)
        if doctor_profile:
            res = WhatsAppService.send_test_doctor_alert(doctor_profile, test_phone=phone)
        else:
            target_phone = phone or user.phone_number
            msg = f"✅ *Virtual Care - Test Notification*\n\nHello {user.full_name},\nYour WhatsApp notification integration is active!"
            res = WhatsAppService.send_message(to_phone=target_phone, message=msg, user=user)

        return success_response(
            data=res,
            message="Test WhatsApp notification dispatched."
        )
