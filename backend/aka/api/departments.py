from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..authentication.utils import build_department_claims


class DepartmentListView(APIView):
    """
    List all departments the current user has access to.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # build_department_claims returns the list of departments with the user's
        # role and sensitivity ceiling for each, as expected by the frontend.
        departments = build_department_claims(request.user)
        return Response(departments)
