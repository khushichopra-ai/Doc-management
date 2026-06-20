from __future__ import annotations

from rest_framework.permissions import BasePermission

from aka.models import User


class IsLead(BasePermission):
    """Allow only the account-level Lead (the system owner)."""

    message = "Only the Lead can perform this action."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.role == User.Role.LEAD)
