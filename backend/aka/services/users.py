from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

User = get_user_model()


@dataclass(slots=True)
class RegistrationResult:
    user: object
    message: str


class UserService:
    """Account registration and the contributor approval workflow.

    Account-level role/approval only — department membership and retrieval RBAC
    are unchanged and handled elsewhere.
    """

    VIEWER_MESSAGE = "Your account has been created. You can log in now."
    CONTRIBUTOR_MESSAGE = "Your contributor request has been submitted and is awaiting Lead approval."

    def register(self, *, name: str, email: str, password: str, role: str) -> RegistrationResult:
        email = email.strip().lower()
        if role not in {User.Role.CONTRIBUTOR, User.Role.VIEWER}:
            # Lead accounts are seeded only; never self-registered.
            raise ValueError("Role must be 'viewer' or 'contributor'.")

        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username=email).exists():
            raise ValueError("An account with this email already exists.")

        is_viewer = role == User.Role.VIEWER
        try:
            with transaction.atomic():
                user = User(
                    username=email,
                    email=email,
                    first_name=name.strip(),
                    org_role=User.OrgRole.MEMBER,
                    role=role,
                    approved=is_viewer,
                    status=User.Status.ACTIVE if is_viewer else User.Status.PENDING,
                )
                user.set_password(password)
                user.save()
        except IntegrityError as exc:
            raise ValueError("An account with this email already exists.") from exc

        message = self.VIEWER_MESSAGE if is_viewer else self.CONTRIBUTOR_MESSAGE
        return RegistrationResult(user=user, message=message)

    def list_pending_contributors(self):
        return User.objects.filter(
            role=User.Role.CONTRIBUTOR,
            status=User.Status.PENDING,
        ).order_by("created_at")

    @transaction.atomic
    def approve_contributor(self, *, contributor, lead) -> object:
        contributor.approved = True
        contributor.status = User.Status.ACTIVE
        contributor.approved_by = lead
        contributor.approved_at = timezone.now()
        contributor.save(update_fields=["approved", "status", "approved_by", "approved_at", "updated_at"])
        return contributor

    @transaction.atomic
    def reject_contributor(self, *, contributor, lead) -> object:
        contributor.approved = False
        contributor.status = User.Status.REJECTED
        contributor.approved_by = lead
        contributor.approved_at = timezone.now()
        contributor.save(update_fields=["approved", "status", "approved_by", "approved_at", "updated_at"])
        return contributor
