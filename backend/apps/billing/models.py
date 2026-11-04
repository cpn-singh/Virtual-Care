"""
Billing & Invoice Models
Author: Financial Systems & Billing Operations Team

Handles trusted server-side pricing, payment gateway transaction tracking,
and immutable financial invoices.
"""

import uuid
from django.db import models
from apps.appointments.models import Appointment
from apps.patients.models import PatientProfile


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='payments')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    provider = models.CharField(max_length=50, default='razorpay')
    
    order_id = models.CharField(max_length=120, unique=True)
    transaction_id = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=120, unique=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.order_id}: {self.currency} {self.amount} ({self.status})"


class Invoice(models.Model):
    STATUS_PAID = 'paid'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PAID, 'Paid'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=60, unique=True)
    
    patient_name = models.CharField(max_length=150)
    doctor_name = models.CharField(max_length=150)
    
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.total_amount}"
