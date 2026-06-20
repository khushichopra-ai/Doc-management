from __future__ import annotations

from django.utils import timezone

from aka.models import Notification, User


class NotificationService:
    def request_created(self, *, recipient: User, title: str, message: str) -> Notification:
        return Notification.objects.create(
            recipient=recipient,
            notification_type=Notification.NotificationType.REQUEST_RECEIVED,
            title=title,
            message=message,
        )

    def approved(self, *, recipient: User, title: str, message: str) -> Notification:
        return Notification.objects.create(
            recipient=recipient,
            notification_type=Notification.NotificationType.APPROVED,
            title=title,
            message=message,
        )

    def rejected(self, *, recipient: User, title: str, message: str) -> Notification:
        return Notification.objects.create(
            recipient=recipient,
            notification_type=Notification.NotificationType.REJECTED,
            title=title,
            message=message,
        )

    def access_granted(self, *, recipient: User, title: str, message: str) -> Notification:
        return Notification.objects.create(
            recipient=recipient,
            notification_type=Notification.NotificationType.ACCESS_GRANTED,
            title=title,
            message=message,
        )

