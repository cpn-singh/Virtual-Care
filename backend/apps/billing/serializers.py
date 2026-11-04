"""
Billing Serializers
Author: Financial Systems & Billing Operations Team
"""

from rest_framework import serializers
from apps.billing.models import Payment, Invoice


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id',
            'appointment_id',
            'amount',
            'currency',
            'provider',
            'order_id',
            'transaction_id',
            'status',
            'created_at',
            'verified_at',
        ]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'patient_name',
            'doctor_name',
            'consultation_fee',
            'tax_amount',
            'total_amount',
            'status',
            'payment',
            'created_at',
        ]
        read_only_fields = fields


class CreateOrderInputSerializer(serializers.Serializer):
    appointment_id = serializers.UUIDField()


class VerifyPaymentInputSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    transaction_id = serializers.CharField(required=False, allow_blank=True, default="")
