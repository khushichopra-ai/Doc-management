from __future__ import annotations

from typing import Any

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate requests from a bearer token or the access cookie.
    """

    def get_raw_token_from_request(self, request: Request) -> str | None:
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                return raw_token.decode("utf-8")
        return request.COOKIES.get("access")

    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        raw_token = self.get_raw_token_from_request(request)
        if raw_token is None:
            return None

        # Treat an expired/invalid/stale cookie as "anonymous" rather than raising:
        # raising here would 401 even AllowAny endpoints (login/refresh), trapping
        # the user once their access cookie expires. Protected views still 401 via
        # IsAuthenticated; the client then refreshes or logs in again.
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None

        request.jwt_claims = dict(validated_token.payload)
        return user, validated_token
