from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers

from aka.models import User


class LoginSerializer(serializers.Serializer):
    # Accepts an email or a username in the same field.
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        identifier = attrs["username"].strip()
        # Allow logging in with email by resolving it to the stored username.
        match = User.objects.filter(email__iexact=identifier).first()
        lookup = match.username if match else identifier

        user = authenticate(username=lookup, password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        # Credential check only; approval gating is applied in the view so it can
        # return a precise message and withhold the auth cookies.
        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6, trim_whitespace=False)
    # Self-registration is limited to viewer/contributor; Lead is seeded only.
    role = serializers.ChoiceField(choices=[User.Role.VIEWER, User.Role.CONTRIBUTOR])


class POCUserSerializer(serializers.Serializer):
    username = serializers.ChoiceField(choices=["alice", "bob", "dave", "lead@aka.local"])


class AuthUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name")

    class Meta:
        model = User
        fields = ("id", "username", "email", "name", "org_role", "role", "status")
