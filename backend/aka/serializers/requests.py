from __future__ import annotations

from rest_framework import serializers

from aka.models import Document, InformationRequest


class InformationRequestCreateSerializer(serializers.Serializer):
    request_text = serializers.CharField()
    reason = serializers.CharField()
    department = serializers.SlugField()
    document_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        document = None
        if attrs.get("document_id"):
            try:
                document = Document.objects.select_related("department").get(id=attrs["document_id"])
            except Document.DoesNotExist as exc:
                raise serializers.ValidationError("Invalid document.") from exc
            if document.department.slug != attrs["department"]:
                raise serializers.ValidationError("Document does not belong to the selected department.")
        attrs["document"] = document
        return attrs


class InformationRequestSerializer(serializers.ModelSerializer):
    requester = serializers.CharField(source="requester.username")
    approver = serializers.CharField(source="approver.username", allow_null=True)
    department = serializers.CharField(source="department.name")
    document = serializers.CharField(source="document.name", allow_null=True)

    class Meta:
        model = InformationRequest
        fields = (
            "id",
            "requester",
            "approver",
            "department",
            "document",
            "request_text",
            "reason",
            "status",
            "approver_note",
            "created_at",
            "decided_at",
            "access_expires_at",
        )
