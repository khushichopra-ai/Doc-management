from __future__ import annotations

from rest_framework import serializers

from aka.models import Department, Document


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    department = serializers.SlugField()
    sensitivity = serializers.ChoiceField(choices=Document.Sensitivity.choices)

    def validate_department(self, value: str) -> Department:
        try:
            return Department.objects.get(slug=value)
        except Department.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid department.") from exc


class DocumentListSerializer(serializers.ModelSerializer):
    uploader = serializers.CharField(source="uploader.username")
    department = serializers.CharField(source="department.name")

    class Meta:
        model = Document
        fields = ("id", "name", "department", "sensitivity", "version", "status", "uploader", "uploaded_at", "file_size")

