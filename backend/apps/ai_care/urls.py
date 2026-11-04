"""
AI Care URL Configuration
Author: Clinical Safety & AI Governance Team
"""

from django.urls import path
from apps.ai_care.views import (
    AICareSessionCreateView,
    AICareSendMessageView,
    AICareHandoffView,
)

urlpatterns = [
    path('sessions/', AICareSessionCreateView.as_view(), name='ai-session-create'),
    path('sessions/<uuid:session_id>/messages/', AICareSendMessageView.as_view(), name='ai-send-message'),
    path('sessions/<uuid:session_id>/handoff/', AICareHandoffView.as_view(), name='ai-handoff'),
]
