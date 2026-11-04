"""
Authentication URL Configuration
Author: Security & Identity Team
"""

from django.urls import path
from apps.accounts.views import (
    RegisterView,
    VerifyEmailOTPView,
    ResendEmailOTPView,
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    MeView,
    DevLatestOTPView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('verify-email-otp/', VerifyEmailOTPView.as_view(), name='auth-verify-email-otp'),
    path('resend-email-otp/', ResendEmailOTPView.as_view(), name='auth-resend-email-otp'),
    path('dev-otp/', DevLatestOTPView.as_view(), name='auth-dev-otp'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='auth-password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    path('me/', MeView.as_view(), name='auth-me'),
]
