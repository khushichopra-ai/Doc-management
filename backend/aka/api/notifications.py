from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aka.models import Notification


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Notification.objects.filter(recipient=request.user).order_by("-created_at")
        data = [
            {
                "id": str(item.id),
                "notification_type": item.notification_type,
                "title": item.title,
                "message": item.message,
                "is_read": item.is_read,
                "created_at": item.created_at,
            }
            for item in items
        ]
        return Response(data)
