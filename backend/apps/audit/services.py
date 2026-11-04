"""
Audit Service Utility
Author: Compliance & Information Security Team
"""

from apps.audit.models import AuditEvent


def log_audit_event(action: str, resource_type: str, actor=None, resource_id: str = "", ip_address: str = None, metadata: dict = None):
    """Safely records a structured audit event without raising exceptions."""
    try:
        AuditEvent.objects.create(
            actor=actor if (actor and actor.is_authenticated) else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            ip_address=ip_address,
            metadata=metadata or {}
        )
    except Exception as e:
        # Never crash the main request if audit logging encounters a database hiccup
        print(f"[Audit Warning] Failed to record audit log: {e}")
