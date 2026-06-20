from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from aka.models import Department, DepartmentMembership, Document, DocumentAccess, InformationRequest, User
from aka.services.notifications import NotificationService


class InformationRequestService:
    def __init__(self, notification_service: NotificationService | None = None) -> None:
        self.notification_service = notification_service or NotificationService()

    def _resolve_approver(self, department: Department) -> User:
        """Route every access request to the account-level Lead (the system owner),
        who is the only role permitted to approve/reject. Falls back to a legacy
        department lead if no account Lead exists."""
        lead = User.objects.filter(role=User.Role.LEAD).order_by("date_joined").first()
        if lead is not None:
            return lead

        legacy_lead = (
            DepartmentMembership.objects.select_related("user")
            .filter(department=department, role=DepartmentMembership.MembershipRole.LEAD)
            .order_by("created_at")
            .first()
        )
        if legacy_lead is not None:
            return legacy_lead.user

        raise ValueError("No approver available.")

    def _enforce_cooldown(self, *, requester: User, department: Department, request_text: str, document: Document | None) -> None:
        since = timezone.now() - timedelta(days=7)
        queryset = InformationRequest.objects.filter(
            requester=requester,
            department=department,
            request_text__iexact=request_text.strip(),
            created_at__gte=since,
            status=InformationRequest.Status.REJECTED,
        )
        if document is not None:
            queryset = queryset.filter(document=document)
        if queryset.exists():
            raise ValueError("Same request is on cooldown for 7 days.")

    def create_request(
        self,
        *,
        requester: User,
        department: Department,
        request_text: str,
        reason: str,
        document: Document | None = None,
    ) -> InformationRequest:
        self._enforce_cooldown(
            requester=requester,
            department=department,
            request_text=request_text,
            document=document,
        )
        approver = self._resolve_approver(department)
        info_request = InformationRequest.objects.create(
            requester=requester,
            approver=approver,
            department=department,
            document=document,
            request_text=request_text,
            reason=reason,
            status=InformationRequest.Status.PENDING,
        )
        self.notification_service.request_created(
            recipient=approver,
            title="New information request",
            message=f"{requester.username} requested access in {department.name}.",
        )
        return info_request

    def list_pending(self, approver: User):
        return InformationRequest.objects.select_related("requester", "department", "document").filter(
            approver=approver,
            status=InformationRequest.Status.PENDING,
        ).order_by("-created_at")

    def approve(self, *, request_obj: InformationRequest, approver_note: str = "") -> InformationRequest:
        expires_at = timezone.now() + timedelta(days=30)
        request_obj.status = InformationRequest.Status.APPROVED
        request_obj.approver_note = approver_note
        request_obj.decided_at = timezone.now()
        request_obj.access_expires_at = expires_at if request_obj.document_id else None
        request_obj.save(update_fields=["status", "approver_note", "decided_at", "access_expires_at", "updated_at"])

        if request_obj.document_id:
            DocumentAccess.objects.update_or_create(
                user=request_obj.requester,
                document=request_obj.document,
                defaults={
                    "granted_by": request_obj.approver,
                    "expires_at": expires_at,
                    "is_active": True,
                },
            )
            self.notification_service.access_granted(
                recipient=request_obj.requester,
                title="Request approved",
                message=f"You can now access {request_obj.document.name}.",
            )
        else:
            self.notification_service.approved(
                recipient=request_obj.requester,
                title="Request approved",
                message="Your request was approved. The document is pending upload.",
            )
        return request_obj

    def reject(self, *, request_obj: InformationRequest, approver_note: str = "") -> InformationRequest:
        request_obj.status = InformationRequest.Status.REJECTED
        request_obj.approver_note = approver_note
        request_obj.decided_at = timezone.now()
        request_obj.save(update_fields=["status", "approver_note", "decided_at", "updated_at"])
        self.notification_service.rejected(
            recipient=request_obj.requester,
            title="Request rejected",
            message=approver_note or "Your request was rejected.",
        )
        return request_obj
