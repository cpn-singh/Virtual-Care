"""
AI Care Serializers
Author: Clinical Safety & AI Governance Team
"""

from rest_framework import serializers
from apps.ai_care.models import AIConversation, AIMessage, AIHandoff


class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = [
            'id',
            'role',
            'content',
            'category',
            'urgency',
            'emergency_action_required',
            'recommended_next_step',
            'created_at',
        ]
        read_only_fields = fields


class AIConversationSerializer(serializers.ModelSerializer):
    messages = AIMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AIConversation
        fields = [
            'id',
            'session_token',
            'title',
            'status',
            'is_emergency',
            'protocol_version',
            'messages',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class SendMessageInputSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=2000)


class AIHandoffSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIHandoff
        fields = [
            'id',
            'conversation',
            'symptom_summary',
            'recommended_specialization',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
