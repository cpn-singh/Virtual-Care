"""
Global DRF Exception Handler
Author: Telehealth Platform Core Team

Formats unhandled exceptions into the unified API error format.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Catch standard DRF exceptions or unexpected server errors
    and format them into our predictable error response schema.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return Response(
            {
                "status": "error",
                "message": "Validation or permission error occurred.",
                "errors": response.data,
            },
            status=response.status_code,
        )

    # Log unexpected 500 exceptions
    logger.exception("Unexpected server error: %s", exc)
    return Response(
        {
            "status": "error",
            "message": "An unexpected server error occurred. Our engineering team has been notified.",
            "errors": {"detail": str(exc)},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
