from __future__ import annotations

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from ..authentication.utils import build_department_claims, build_refresh_token
from aka.serializers.auth import AuthUserSerializer, LoginSerializer, POCUserSerializer, RegisterSerializer
from aka.services.users import UserService


ACCESS_COOKIE_NAME = "access"
REFRESH_COOKIE_NAME = "refresh"


def set_auth_cookies(response: HttpResponse, access_token: str, refresh_token: str) -> None:
    secure = not settings.DEBUG
    cookie_kwargs = {
        "httponly": True,
        "secure": secure,
        "samesite": "Lax",
        "path": "/",
    }
    response.set_cookie(ACCESS_COOKIE_NAME, access_token, max_age=60 * 60, **cookie_kwargs)
    response.set_cookie(REFRESH_COOKIE_NAME, refresh_token, max_age=60 * 60 * 24 * 7, **cookie_kwargs)


def clear_auth_cookies(response: HttpResponse) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = UserService().register(
                name=serializer.validated_data["name"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                role=serializer.validated_data["role"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "detail": result.message,
                "user": AuthUserSerializer(result.user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Approval gating (contributors require Lead approval before first login).
        if user.status == get_user_model().Status.REJECTED:
            return Response(
                {"detail": "Your contributor request was rejected."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user.role == get_user_model().Role.CONTRIBUTOR and not user.can_login:
            return Response(
                {"detail": "Your account is awaiting approval from the Lead."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = build_refresh_token(user)
        access = refresh.access_token
        access["user_id"] = str(user.id)
        access["org_role"] = user.org_role.lower()
        access["departments"] = build_department_claims(user)

        response = Response(
            {
                "user": AuthUserSerializer(user).data,
                "departments": access["departments"],
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, str(access), str(refresh))
        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({"detail": "Logged out."}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        django_logout(request)
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token_value = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not refresh_token_value:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token_value)
        except TokenError as exc:
            raise InvalidToken("Invalid refresh token") from exc

        User = get_user_model()
        try:
            user = User.objects.get(id=refresh["user_id"])
        except User.DoesNotExist:
            return Response({"detail": "Invalid token user."}, status=status.HTTP_401_UNAUTHORIZED)

        new_refresh = build_refresh_token(user)
        new_access = new_refresh.access_token
        new_access["user_id"] = str(user.id)
        new_access["org_role"] = user.org_role.lower()
        new_access["departments"] = build_department_claims(user)

        response = Response(
            {
                "user": AuthUserSerializer(user).data,
                "departments": new_access["departments"],
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, str(new_access), str(new_refresh))
        return response


class POCLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = POCUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        User = get_user_model()
        user = User.objects.get(username=serializer.validated_data["username"])

        # Enforce approval gating — same rules as LoginView.
        if user.status == User.Status.REJECTED:
            return Response(
                {"detail": "Your contributor request was rejected."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user.role == User.Role.CONTRIBUTOR and not user.can_login:
            return Response(
                {"detail": "Your account is awaiting approval from the Lead."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = build_refresh_token(user)
        access = refresh.access_token
        access["user_id"] = str(user.id)
        access["name"] = user.get_full_name() or user.username
        access["org_role"] = user.org_role.lower()
        access["departments"] = build_department_claims(user)
        return Response(
            {
                "token": str(access),
                "user": AuthUserSerializer(user).data,
                "departments": access["departments"],
            },
            status=status.HTTP_200_OK,
        )
