from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aka.models import Department, InformationRequest
from aka.permissions.rbac import RBACPermission
from aka.serializers.requests import InformationRequestCreateSerializer, InformationRequestSerializer
from aka.services.requests import InformationRequestService


class InformationRequestCreateView(APIView):
    permission_classes = [IsAuthenticated, RBACPermission]

    def post(self, request):
        serializer = InformationRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = get_object_or_404(Department, slug=serializer.validated_data["department"])
        service = InformationRequestService()
        try:
            info_request = service.create_request(
                requester=request.user,
                department=department,
                request_text=serializer.validated_data["request_text"],
                reason=serializer.validated_data["reason"],
                document=serializer.validated_data.get("document"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InformationRequestSerializer(info_request).data, status=status.HTTP_201_CREATED)


class PendingRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = InformationRequestService()
        requests = service.list_pending(request.user)
        return Response(InformationRequestSerializer(requests, many=True).data)


class ApproveRequestView(APIView):
    permission_classes = [IsAuthenticated, RBACPermission]

    def post(self, request, request_id):
        info_request = get_object_or_404(InformationRequest, id=request_id)
        service = InformationRequestService()
        updated = service.approve(request_obj=info_request, approver_note=request.data.get("note", ""))
        return Response(InformationRequestSerializer(updated).data)


class RejectRequestView(APIView):
    permission_classes = [IsAuthenticated, RBACPermission]

    def post(self, request, request_id):
        info_request = get_object_or_404(InformationRequest, id=request_id)
        service = InformationRequestService()
        updated = service.reject(request_obj=info_request, approver_note=request.data.get("note", ""))
        return Response(InformationRequestSerializer(updated).data)
