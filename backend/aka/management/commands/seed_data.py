from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from aka.models import Department, DepartmentMembership, Document


class Command(BaseCommand):
    help = "Seed core RBAC users, departments, and memberships."

    def handle(self, *args, **options):
        User = get_user_model()

        departments = {
            "AI Team": {"slug": "ai-team", "type": "ai"},
            "AI Showcases": {"slug": "ai-showcases", "type": "ai_showcases"},
            "Sales": {"slug": "sales", "type": "sales"},
            "CeFi": {"slug": "cefi", "type": "vertical"},
            "DeFi": {"slug": "defi", "type": "vertical"},
        }

        Department.objects.exclude(name__in=departments.keys()).delete()

        department_objects = {}
        for name, payload in departments.items():
            department_objects[name], _ = Department.objects.get_or_create(
                name=name,
                slug=payload["slug"],
                defaults=payload,
            )
            Department.objects.filter(pk=department_objects[name].pk).update(**payload)

        # The single account-level Lead and system owner. Created only via seed
        # (no Lead registration). Approves/rejects contributor sign-ups and holds
        # lead membership in every department so it can manage all documents.
        lead, _ = User.objects.update_or_create(
            username="lead@aka.local",
            defaults={
                "email": "lead@aka.local",
                "first_name": "System Lead",
                "org_role": User.OrgRole.SUPER_ADMIN,
                "role": User.Role.LEAD,
                "approved": True,
                "status": User.Status.ACTIVE,
            },
        )
        # Alice is a department lead (knowledge owner) used by the existing
        # information-request demo. Account-level role is contributor so the single
        # account Lead above stays unique; her per-department lead powers are
        # unchanged (they come from DepartmentMembership).
        alice, _ = User.objects.update_or_create(
            username="alice",
            defaults={
                "email": "alice@example.com",
                "org_role": User.OrgRole.SUPER_ADMIN,
                "role": User.Role.CONTRIBUTOR,
                "approved": True,
                "status": User.Status.ACTIVE,
            },
        )
        # Bob is the Viewer (also cross-department reader on AI Showcases).
        bob, _ = User.objects.update_or_create(
            username="bob",
            defaults={
                "email": "bob@example.com",
                "org_role": User.OrgRole.MEMBER,
                "role": User.Role.VIEWER,
                "approved": True,
                "status": User.Status.ACTIVE,
            },
        )
        # Dave is the AI Team Contributor.
        dave, _ = User.objects.update_or_create(
            username="dave",
            defaults={
                "email": "dave@example.com",
                "org_role": User.OrgRole.MEMBER,
                "role": User.Role.CONTRIBUTOR,
                "approved": True,
                "status": User.Status.ACTIVE,
            },
        )

        memberships = [
            (lead, department_objects["AI Team"], "lead", "restricted"),
            (lead, department_objects["AI Showcases"], "lead", "restricted"),
            (lead, department_objects["Sales"], "lead", "restricted"),
            (lead, department_objects["CeFi"], "lead", "restricted"),
            (lead, department_objects["DeFi"], "lead", "restricted"),
            (alice, department_objects["AI Team"], "lead", "restricted"),
            # AI Showcases is the AI team's cross-readable space; Alice leads it too
            # so AI-Showcases requests have an in-department approver.
            (alice, department_objects["AI Showcases"], "lead", "restricted"),
            # Alice also leads the new verticals so they have an in-dept approver.
            (alice, department_objects["CeFi"], "lead", "restricted"),
            (alice, department_objects["DeFi"], "lead", "restricted"),
            (dave, department_objects["AI Team"], "contributor", "internal"),
            (bob, department_objects["Sales"], "viewer", "open"),
            (bob, department_objects["AI Showcases"], "viewer", "open"),
        ]

        for user, department, role, ceiling in memberships:
            DepartmentMembership.objects.update_or_create(
                user=user,
                department=department,
                defaults={
                    "role": role,
                    "sensitivity_ceiling": ceiling,
                    "granted_via": "direct",
                },
            )

        # Remove Charlie (redundant Viewer). Reassign any documents he uploaded to
        # Alice first so they survive (Document.uploader cascades on delete).
        stale_charlie = User.objects.filter(username="charlie").first()
        if stale_charlie is not None:
            Document.objects.filter(uploader=stale_charlie).update(uploader=alice)
            stale_charlie.delete()

        # Lead credentials are created manually here (no registration page).
        lead.set_password("Lead@123")
        lead.save(update_fields=["password"])

        # Existing demo members keep a shared password for convenience.
        demo_password = "demo12345"
        for user in (alice, bob, dave):
            user.set_password(demo_password)
            user.save(update_fields=["password"])

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded RBAC data. Lead: lead@aka.local / Lead@123. "
                f"Demo members (alice, bob, dave): {demo_password}."
            )
        )
