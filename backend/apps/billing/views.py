"""
Billing API Views
Author: Financial Systems & Billing Operations Team

Endpoints for:
- Initiating payment order with server-side fee calculation
- Verifying gateway payments and minting invoices
- Patient & admin invoice history
"""

from rest_framework.views import APIView
from rest_framework import permissions, status
from apps.billing.models import Payment, Invoice
from apps.billing.serializers import (
    PaymentSerializer,
    InvoiceSerializer,
    CreateOrderInputSerializer,
    VerifyPaymentInputSerializer,
)
from apps.billing.services.payment_service import PaymentService
from apps.appointments.models import Appointment
from apps.patients.models import PatientProfile
from common.roles import UserRole
from common.responses import success_response, error_response


class CreatePaymentOrderView(APIView):
    """
    POST /api/v1/payments/create-order/
    Initializes a payment order for an appointment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        appointment_id = serializer.validated_data['appointment_id']
        appointment = Appointment.objects.select_related('doctor', 'patient__user').filter(id=appointment_id).first()

        if not appointment:
            return error_response(message="Appointment not found.", http_status=status.HTTP_404_NOT_FOUND)

        if appointment.patient.user != request.user and request.user.role != UserRole.ADMIN:
            return error_response(message="Unauthorized to pay for this appointment.", http_status=status.HTTP_403_FORBIDDEN)

        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        payment = PaymentService.create_order(appointment, patient_profile)

        return success_response(
            data=PaymentSerializer(payment).data,
            message="Payment order created successfully.",
            http_status=status.HTTP_201_CREATED
        )


class VerifyPaymentView(APIView):
    """
    POST /api/v1/payments/verify/
    Verifies transaction settlement and generates invoice.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        order_id = serializer.validated_data['order_id']
        transaction_id = serializer.validated_data.get('transaction_id')

        success, message, payment = PaymentService.verify_and_settle_payment(order_id, transaction_id)
        if not success:
            return error_response(message=message)

        invoice = getattr(payment, 'invoice', None)
        invoice_data = InvoiceSerializer(invoice).data if invoice else None

        return success_response(
            data={
                "payment": PaymentSerializer(payment).data,
                "invoice": invoice_data,
            },
            message=message
        )


class PaymentListView(APIView):
    """
    GET /api/v1/payments/
    Lists payments for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == UserRole.PATIENT:
            payments = Payment.objects.filter(patient__user=user)
        elif user.role == UserRole.ADMIN:
            payments = Payment.objects.all()
        else:
            payments = Payment.objects.none()

        serializer = PaymentSerializer(payments, many=True)
        return success_response(data=serializer.data)


class InvoiceListView(APIView):
    """
    GET /api/v1/invoices/
    Lists issued invoices.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == UserRole.PATIENT:
            invoices = Invoice.objects.filter(payment__patient__user=user)
        elif user.role == UserRole.ADMIN:
            invoices = Invoice.objects.all()
        else:
            invoices = Invoice.objects.none()

        serializer = InvoiceSerializer(invoices, many=True)
        return success_response(data=serializer.data)


class InvoiceDetailView(APIView):
    """
    GET /api/v1/invoices/<id>/
    Fetch single invoice.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, invoice_id):
        invoice = Invoice.objects.select_related('payment__patient__user').filter(id=invoice_id).first()
        if not invoice:
            return error_response(message="Invoice not found.", http_status=status.HTTP_404_NOT_FOUND)

        if invoice.payment.patient.user != request.user and request.user.role != UserRole.ADMIN:
            return error_response(message="Unauthorized to view this invoice.", http_status=status.HTTP_403_FORBIDDEN)

        serializer = InvoiceSerializer(invoice)
        return success_response(data=serializer.data)
