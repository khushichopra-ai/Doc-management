from django.contrib import admin

from .models import BaseModel, Department, DepartmentMembership, Document, DocumentAccess, InformationRequest, Notification, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "org_role", "is_staff", "is_active")
    search_fields = ("username", "email")
    list_filter = ("org_role", "is_staff", "is_active")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "type", "created_at", "updated_at")
    search_fields = ("name", "slug", "type")
    readonly_fields = ("id", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DepartmentMembership)
class DepartmentMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "role", "sensitivity_ceiling", "granted_via")
    search_fields = ("user__username", "user__email", "department__name")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "uploader", "sensitivity", "status", "version", "file_size")
    search_fields = ("name", "department__name", "department__slug", "uploader__username")


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "document", "is_active", "expires_at", "granted_by")
    search_fields = ("user__username", "document__name")


@admin.register(InformationRequest)
class InformationRequestAdmin(admin.ModelAdmin):
    list_display = ("requester", "department", "document", "status", "approver", "created_at")
    search_fields = ("requester__username", "department__name", "document__name")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "title", "is_read", "created_at")
    search_fields = ("recipient__username", "title")
