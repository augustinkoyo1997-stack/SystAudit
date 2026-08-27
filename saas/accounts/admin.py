from django.contrib import admin

from .models import License


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "is_active",
        "created_at",
        "expires_at",
    )

    list_filter = (
        "plan",
        "is_active",
    )

    search_fields = (
        "user__username",
        "user__email",
    )