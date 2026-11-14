from django.urls import path
from apps.notifications.views import NotificationListView, WhatsAppTestView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('whatsapp/test/', WhatsAppTestView.as_view(), name='whatsapp-test'),
]
