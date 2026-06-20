from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aka.models import User
from aka.permissions.roles import IsLead
from aka.services.users import UserService


def _serialize_contributor(user: User) -> dict:
    return {
        "id": str(user.id),
        "name": user.first_name or user.username,
        "email": user.email,
        "status": user.status,
        "requested_at": user.created_at,
    }


class PendingContributorListView(APIView):
    permission_classes = [IsAuthenticated, IsLead]

    def get(self, request):
        pending = UserService().list_pending_contributors()
        return Response([_serialize_contributor(u) for u in pending])


class ApproveContributorView(APIView):
    permission_classes = [IsAuthenticated, IsLead]

    def post(self, request, user_id):
        contributor = get_object_or_404(User, id=user_id, role=User.Role.CONTRIBUTOR)
        updated = UserService().approve_contributor(contributor=contributor, lead=request.user)
        return Response(_serialize_contributor(updated), status=status.HTTP_200_OK)


class RejectContributorView(APIView):
    permission_classes = [IsAuthenticated, IsLead]

    def post(self, request, user_id):
        contributor = get_object_or_404(User, id=user_id, role=User.Role.CONTRIBUTOR)
        updated = UserService().reject_contributor(contributor=contributor, lead=request.user)
        return Response(_serialize_contributor(updated), status=status.HTTP_200_OK)
