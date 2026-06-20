from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aka.permissions.rbac import RBACPermission
from aka.services.rag import RAGService


class ChatQueryView(APIView):
    permission_classes = [IsAuthenticated, RBACPermission]

    def post(self, request):
        question = request.data.get("question", "").strip()
        department = request.data.get("department", "").strip()
        if not question or not department:
            return Response({"detail": "question and department are required."}, status=status.HTTP_400_BAD_REQUEST)
        rag_service = RAGService()
        result = rag_service.answer(
            question=question,
            aka_filter=getattr(request, "aka_filter", {}),
            department=department,
        )
        return Response(
            {
                "answer": result.answer,
                "sources": result.sources,
                "department": result.department,
            }
        )
