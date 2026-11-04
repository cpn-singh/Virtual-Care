"""
Billing URL Configuration
Author: Financial Systems & Billing Operations Team
"""

from django.urls import path
from apps.billing.views import (
    CreatePaymentOrderView,
    VerifyPaymentView,
    PaymentListView,
    InvoiceListView,
    InvoiceDetailView,
)

urlpatterns = [
    path('payments/create-order/', CreatePaymentOrderView.as_view(), name='payment-create-order'),
    path('payments/verify/', VerifyPaymentView.as_view(), name='payment-verify'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<uuid:invoice_id>/', InvoiceDetailView.as_view(), name='invoice-detail'),
]
