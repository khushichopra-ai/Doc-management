from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, BaseModel):
    class OrgRole(models.TextChoices):
        MEMBER = "member", "Member"
        SUPER_ADMIN = "super_admin", "Super Admin"

    class Role(models.TextChoices):
        LEAD = "lead", "Lead"
        CONTRIBUTOR = "contributor", "Contributor"
        VIEWER = "viewer", "Viewer"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    org_role = models.CharField(max_length=20, choices=OrgRole.choices, default=OrgRole.MEMBER)

    # Account-level role and approval workflow (distinct from per-department
    # DepartmentMembership.role, which continues to drive retrieval RBAC).
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_users",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users"

    @property
    def can_login(self) -> bool:
        return self.status == self.Status.ACTIVE and self.approved


class Department(BaseModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True, null=True, blank=True)
    type = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        db_table = "departments"


class DepartmentMembership(BaseModel):
    class MembershipRole(models.TextChoices):
        LEAD = "lead", "Lead"
        CONTRIBUTOR = "contributor", "Contributor"
        VIEWER = "viewer", "Viewer"

    class SensitivityCeiling(models.TextChoices):
        OPEN = "open", "Open"
        INTERNAL = "internal", "Internal"
        RESTRICTED = "restricted", "Restricted"
        CONFIDENTIAL = "confidential", "Confidential"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="department_memberships")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=MembershipRole.choices, default=MembershipRole.CONTRIBUTOR)
    sensitivity_ceiling = models.CharField(
        max_length=20, choices=SensitivityCeiling.choices, default=SensitivityCeiling.INTERNAL
    )
    granted_via = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "department_memberships"
        constraints = [
            models.UniqueConstraint(fields=["user", "department"], name="uniq_department_membership"),
        ]


class Document(BaseModel):
    class Sensitivity(models.TextChoices):
        OPEN = "open", "Open"
        INTERNAL = "internal", "Internal"
        RESTRICTED = "restricted", "Restricted"
        CONFIDENTIAL = "confidential", "Confidential"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUPERSEDED = "superseded", "Superseded"
        DELETED = "deleted", "Deleted"

    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="documents")
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_documents")
    sensitivity = models.CharField(max_length=20, choices=Sensitivity.choices, default=Sensitivity.INTERNAL)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    file_size = models.PositiveBigIntegerField(default=0)
    mime_type = models.CharField(max_length=120, blank=True)
    chunk_count = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents"


class DocumentAccess(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="document_access_grants")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="access_grants")
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_document_access_grants",
    )

    class Meta:
        db_table = "document_access"
        constraints = [
            models.UniqueConstraint(fields=["user", "document"], name="uniq_document_access"),
        ]


class InformationRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ESCALATED = "escalated", "Escalated"

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="information_requests")
    approver = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_information_requests"
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="information_requests")
    document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, blank=True, related_name="information_requests"
    )
    request_text = models.TextField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approver_note = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    access_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "information_requests"


class Notification(BaseModel):
    class NotificationType(models.TextChoices):
        REQUEST_RECEIVED = "request_received", "Request Received"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ACCESS_GRANTED = "access_granted", "Access Granted"

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices, default=NotificationType.REQUEST_RECEIVED
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
