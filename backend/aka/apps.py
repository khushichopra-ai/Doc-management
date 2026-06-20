from django.apps import AppConfig


def _enable_sqlite_wal(sender, connection, **kwargs):
    """Enable WAL + a relaxed sync on each SQLite connection.

    WAL lets concurrent readers proceed while a write is in flight, which (with
    the connection busy-timeout) eliminates the "database is locked" errors that
    surface when the UI polls while an upload is writing.
    """
    if connection.vendor == "sqlite":
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")


class AkaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aka"
    verbose_name = "Antier Knowledge Assistant"

    def ready(self) -> None:
        from django.db.backends.signals import connection_created

        connection_created.connect(_enable_sqlite_wal, dispatch_uid="aka_sqlite_wal")
