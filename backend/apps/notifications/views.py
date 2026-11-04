"""
Notifications API Views
Author: Communication Systems Team
"""

from rest_framework.views import APIView
from rest_framework import permissions, serializers
from apps.notifications.models import Notification
from common.responses import success_response


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:30]
        return success_response(data=NotificationSerializer(notifs, many=True).data)

    def post(self, request):
        """Mark all notifications as read."""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(message="All notifications marked as read.")
