from django.contrib import admin

from .models import License, ManagedComputer, RepairIntervention, WorkspaceInvitation


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


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "workspace", "invited_by", "created_at", "expires_at", "accepted_at")
    list_filter = ("created_at", "expires_at", "accepted_at")
    search_fields = ("email", "workspace__name", "invited_by__email")
    readonly_fields = ("token", "created_at", "accepted_at")


@admin.register(ManagedComputer)
class ManagedComputerAdmin(admin.ModelAdmin):
    list_display = ("asset_tag", "name", "workspace", "licensed_device", "status", "purchase_cost_xof", "updated_at")
    list_filter = ("status", "workspace")
    search_fields = ("asset_tag", "name", "brand", "model_name", "serial_number", "assigned_to")
    readonly_fields = ("asset_tag", "created_at", "updated_at")


@admin.register(RepairIntervention)
class RepairInterventionAdmin(admin.ModelAdmin):
    list_display = ("computer", "performed_at", "title", "cost_xof", "technician")
    list_filter = ("performed_at",)
    search_fields = ("computer__asset_tag", "computer__name", "title", "technician")
