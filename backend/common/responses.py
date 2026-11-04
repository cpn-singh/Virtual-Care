"""
Standardized API Responses
Author: Telehealth Platform Core Team

Ensures all JSON responses from our APIs follow a predictable contract:
Success: { "status": "success", "message": "...", "data": {...} }
Error:   { "status": "error", "message": "...", "errors": {...} }
"""

from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Operation successful", http_status=status.HTTP_200_OK):
    """Return a clean standardized success response."""
    payload = {
        "status": "success",
        "message": message,
        "data": data if data is not None else {}
    }
    return Response(payload, status=http_status)


def error_response(message="Operation failed", errors=None, http_status=status.HTTP_400_BAD_REQUEST):
    """Return a clean standardized error response."""
    payload = {
        "status": "error",
        "message": message,
        "errors": errors if errors is not None else {}
    }
    return Response(payload, status=http_status)
