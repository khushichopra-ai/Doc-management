from __future__ import annotations

from dataclasses import dataclass, field

from rest_framework.exceptions import PermissionDenied

from aka.models import DocumentAccess, User


SENSITIVITY_ORDER = ["open", "internal", "restricted", "confidential"]
ROLE_ALLOWED_ACTIONS = {
    "viewer": {"query"},
    "contributor": {"query", "upload"},
    "lead": {"query", "upload", "delete", "approve", "reject"},
}


def _max_sensitivity(ceiling: str) -> list[str]:
    if ceiling not in SENSITIVITY_ORDER:
        return ["open"]
    end = SENSITIVITY_ORDER.index(ceiling) + 1
    return SENSITIVITY_ORDER[:end]


@dataclass
class RBACScope:
    """A single department namespace paired with the sensitivity levels the user
    may read *in that department*. Keeping levels per-namespace prevents a high
    ceiling in one department from leaking high-sensitivity docs in another."""

    namespace: str
    allowed_sensitivity: list[str] = field(default_factory=list)


@dataclass
class RBACFilter:
    scopes: list[RBACScope] = field(default_factory=list)
    extra_doc_ids: list[str] = field(default_factory=list)


class RBACService:
    @staticmethod
    def resolve_departments(claims: list[dict[str, str]]) -> list[str]:
        return sorted({claim["dept_slug"] for claim in claims if claim.get("dept_slug")})

    @staticmethod
    def resolve_sensitivity(user: User, claims: list[dict[str, str]]) -> list[str]:
        sensitivities: set[str] = set()
        for claim in claims:
            sensitivities.update(_max_sensitivity(claim.get("sensitivity_ceiling", "open")))
        if user.org_role == User.OrgRole.SUPER_ADMIN:
            sensitivities.update(SENSITIVITY_ORDER)
        return sorted(sensitivities, key=SENSITIVITY_ORDER.index)

    @staticmethod
    def resolve_document_overrides(user: User) -> list[str]:
        return list(
            DocumentAccess.objects.filter(user=user, is_active=True)
            .values_list("document_id", flat=True)
        )

    @staticmethod
    def _levels_for(user: User, ceiling: str) -> list[str]:
        # Sensitivity is governed strictly by the role-derived ceiling so that the
        # Role x Sensitivity matrix holds (e.g. a contributor never reads restricted
        # docs). Beyond-ceiling access is granted per-document via DocumentAccess.
        return _max_sensitivity(ceiling)

    @classmethod
    def build_filter(cls, user: User, claims: list[dict[str, str]]) -> RBACFilter:
        scopes: list[RBACScope] = []
        for claim in claims:
            slug = claim.get("dept_slug")
            if not slug:
                continue
            scopes.append(
                RBACScope(
                    namespace=slug,
                    allowed_sensitivity=cls._levels_for(user, claim.get("sensitivity_ceiling", "open")),
                )
            )
        return RBACFilter(
            scopes=scopes,
            extra_doc_ids=[str(doc_id) for doc_id in cls.resolve_document_overrides(user)],
        )

    @staticmethod
    def resolve_action_from_request(request) -> str | None:
        if getattr(request, "path", "").endswith("/documents/upload/") and request.method == "POST":
            return "upload"
        if getattr(request, "path", "").endswith("/requests/") and request.method == "POST":
            return "request"
        if "/requests/" in getattr(request, "path", "") and request.method == "POST":
            if request.path.endswith("/approve/"):
                return "approve"
            if request.path.endswith("/reject/"):
                return "reject"
        data = getattr(request, "data", {})
        post_data = getattr(request, "POST", {})
        if request.method == "GET":
            return "query"
        if request.method == "POST":
            return data.get("action") or post_data.get("action") or "query"
        if request.method == "DELETE":
            return "delete"
        return None

    @staticmethod
    def resolve_department_from_request(request) -> str | None:
        data = getattr(request, "data", {})
        post_data = getattr(request, "POST", {})
        query_params = getattr(request, "query_params", request.GET)
        return (
            data.get("department")
            or data.get("department_slug")
            or post_data.get("department")
            or post_data.get("department_slug")
            or query_params.get("department")
            or query_params.get("department_slug")
        )

    @staticmethod
    def resolve_department_from_document_id(document_id: str) -> str | None:
        from aka.models import Document

        document = Document.objects.select_related("department").filter(id=document_id).first()
        return document.department.slug if document else None

    @staticmethod
    def resolve_department_from_information_request(request_id: str) -> str | None:
        from aka.models import InformationRequest

        info_request = InformationRequest.objects.select_related("department").filter(id=request_id).first()
        return info_request.department.slug if info_request else None

    @staticmethod
    def has_document_access_in_department(user: User, department_slug: str) -> bool:
        from aka.models import DocumentAccess

        return DocumentAccess.objects.filter(
            user=user,
            is_active=True,
            document__department__slug=department_slug,
        ).exists()

    @staticmethod
    def _find_membership_claim(claims: list[dict[str, str]], department_slug: str) -> dict[str, str] | None:
        for claim in claims:
            if claim.get("dept_slug") == department_slug or claim.get("dept_name") == department_slug:
                return claim
        return None

    @classmethod
    def authorize_request(cls, user: User, claims: list[dict[str, str]], request, view_kwargs: dict | None = None) -> RBACFilter:
        view_kwargs = view_kwargs or {}
        department_slug = cls.resolve_department_from_request(request)
        action = cls.resolve_action_from_request(request)
        if not department_slug and action == "delete" and view_kwargs.get("document_id"):
            department_slug = cls.resolve_department_from_document_id(str(view_kwargs["document_id"]))
        if not department_slug and action in {"approve", "reject"} and view_kwargs.get("request_id"):
            department_slug = cls.resolve_department_from_information_request(str(view_kwargs["request_id"]))

        if not department_slug or not action:
            raise PermissionDenied("Department and action are required.")

        if action == "request":
            return cls.build_filter(user, claims)

        membership_claim = cls._find_membership_claim(claims, department_slug)
        if membership_claim is None and action == "query" and cls.has_document_access_in_department(user, department_slug):
            return cls.build_filter(user, claims)
        if membership_claim is None:
            raise PermissionDenied("No membership in requested department.")

        role = membership_claim.get("role", "viewer")
        if action not in ROLE_ALLOWED_ACTIONS.get(role, set()):
            raise PermissionDenied("Role does not allow this action.")

        return cls.build_filter(user, claims)
