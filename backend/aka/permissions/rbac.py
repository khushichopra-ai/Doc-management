from __future__ import annotations

from rest_framework.permissions import BasePermission

from aka.services.rbac import RBACService


class RBACPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            request.aka_filter = {"scopes": [], "extra_doc_ids": []}
            return False

        claims = getattr(request, "jwt_claims", {})
        departments = claims.get("departments", []) if isinstance(claims, dict) else []
        rbac_filter = RBACService.authorize_request(user, departments, request, getattr(view, "kwargs", {}))
        request.aka_filter = {
            "scopes": [
                {"namespace": scope.namespace, "allowed_sensitivity": scope.allowed_sensitivity}
                for scope in rbac_filter.scopes
            ],
            "extra_doc_ids": rbac_filter.extra_doc_ids,
        }
        return True
