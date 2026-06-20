"""URL routing for the single ``aka`` application."""
from django.http import JsonResponse
from django.urls import path

from aka.api.auth import LoginView, LogoutView, POCLoginView, RefreshView, RegisterView
from aka.api.chat import ChatQueryView
from aka.api.contributors import ApproveContributorView, PendingContributorListView, RejectContributorView
from aka.api.departments import DepartmentListView
from aka.api.documents import DocumentDetailView, DocumentListView, DocumentUploadView
from aka.api.notifications import NotificationListView
from aka.api.requests import ApproveRequestView, InformationRequestCreateView, PendingRequestListView, RejectRequestView


def health(_request) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "aka"})


urlpatterns = [
    path("health/", health, name="health"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("poc/login/", POCLoginView.as_view(), name="poc-login"),
    path("contributors/pending/", PendingContributorListView.as_view(), name="contributors-pending"),
    path("contributors/<uuid:user_id>/approve/", ApproveContributorView.as_view(), name="contributors-approve"),
    path("contributors/<uuid:user_id>/reject/", RejectContributorView.as_view(), name="contributors-reject"),
    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/<uuid:document_id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("chat/query/", ChatQueryView.as_view(), name="chat-query"),
    path("requests/", InformationRequestCreateView.as_view(), name="request-create"),
    path("requests/pending/", PendingRequestListView.as_view(), name="request-pending"),
    path("requests/<uuid:request_id>/approve/", ApproveRequestView.as_view(), name="request-approve"),
    path("requests/<uuid:request_id>/reject/", RejectRequestView.as_view(), name="request-reject"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
]
