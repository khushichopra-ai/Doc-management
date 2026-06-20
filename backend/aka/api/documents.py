from __future__ import annotations

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aka.models import Document
from aka.permissions.rbac import RBACPermission
from aka.serializers.documents import DocumentListSerializer, DocumentUploadSerializer
from aka.services.documents import DocumentService


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, RBACPermission]

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = DocumentService()
        try:
            result = service.upload(
                uploaded_file=request.FILES["file"],
                department_slug=serializer.validated_data["department"].slug,
                sensitivity=serializer.validated_data["sensitivity"],
                user=request.user,
            )
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "document_id": str(result.document.id),
                "chunk_count": result.chunk_count,
                "status": result.document.status,
            },
            status=status.HTTP_201_CREATED,
        )


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated, RBACPermission]

    def get(self, request):
        department_slug = request.query_params.get("department")
        if not department_slug:
            return Response({"detail": "department is required."}, status=status.HTTP_400_BAD_REQUEST)

        aka_filter = getattr(request, "aka_filter", {})
        dept_scope = next(
            (s for s in aka_filter.get("scopes", []) if s.get("namespace") == department_slug),
            None,
        )
        allowed = set(dept_scope["allowed_sensitivity"]) if dept_scope else set()
        extra_doc_ids = set(aka_filter.get("extra_doc_ids", []))

        # Return every active document in the department (membership is already
        # enforced by RBACPermission). Documents above the user's sensitivity are
        # returned but flagged inaccessible so the UI can grey them and offer a
        # "Request Access" action — rather than hiding them entirely.
        documents = Document.objects.select_related("department", "uploader").filter(
            department__slug=department_slug,
            status=Document.Status.ACTIVE,
        ).order_by("-version", "-created_at")

        payload = []
        for item, data in zip(documents, DocumentListSerializer(documents, many=True).data):
            data["accessible"] = item.sensitivity in allowed or str(item.id) in extra_doc_ids
            payload.append(data)
        return Response(payload)


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated, RBACPermission]

    def delete(self, request, document_id):
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        service = DocumentService()
        service.delete_document(document)
        return Response(status=status.HTTP_204_NO_CONTENT)
