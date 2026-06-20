from __future__ import annotations

from rest_framework_simplejwt.tokens import RefreshToken

from aka.models import Department, User


# Account role -> the highest sensitivity it may read (the Role x Sensitivity
# matrix). Everyone can see every department; what they can READ inside each is
# gated by this ceiling. Restricted/Confidential beyond the ceiling is unlocked
# per-document via an approved access request (DocumentAccess).
ROLE_CEILING = {
    User.Role.LEAD: "restricted",
    User.Role.CONTRIBUTOR: "internal",
    User.Role.VIEWER: "open",
}


def build_department_claims(user: User) -> list[dict[str, str]]:
    """Every authenticated user gets a claim for EVERY department, with their
    account role and the matching sensitivity ceiling. Department visibility is
    universal; sensitivity is enforced per role at retrieval time."""
    role = (user.role or User.Role.VIEWER).lower()
    ceiling = ROLE_CEILING.get(role, "open")

    claims: list[dict[str, str]] = []
    for department in Department.objects.all().order_by("name"):
        claims.append(
            {
                "dept_name": department.name,
                "dept_slug": department.slug,
                "role": role,
                "sensitivity_ceiling": ceiling,
                "granted_via": "role",
            }
        )
    return claims


def build_refresh_token(user: User) -> RefreshToken:
    token = RefreshToken.for_user(user)
    token["user_id"] = str(user.id)
    token["org_role"] = user.org_role.lower()
    token["departments"] = build_department_claims(user)
    return token
