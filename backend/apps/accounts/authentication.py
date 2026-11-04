"""
Custom Bearer Token Authentication
Author: Security & Identity Team

Extracts 'Authorization: Bearer <key>' or 'Authorization: Token <key>'
and validates token expiration and active status.
"""

from rest_framework import authentication, exceptions
from apps.accounts.models import AuthToken


class TokenAuthentication(authentication.BaseAuthentication):
    """
    Simple, secure token authentication using the custom AuthToken table.
    """
    keyword = 'Bearer'
    alt_keyword = 'Token'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2:
            return None

        prefix, key = parts[0], parts[1]
        if prefix.lower() not in (self.keyword.lower(), self.alt_keyword.lower()):
            return None

        try:
            token = AuthToken.objects.select_related('user').get(key=key)
        except AuthToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid authentication token.")

        if not token.is_valid():
            raise exceptions.AuthenticationFailed("Authentication token has expired. Please log in again.")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("This user account is inactive or suspended.")

        # Update last used timestamp
        token.save(update_fields=['last_used_at'])

        return (token.user, token)

    def authenticate_header(self, request):
        return self.keyword
