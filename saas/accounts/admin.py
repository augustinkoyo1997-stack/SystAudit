from django.contrib import admin

from .models import DeploymentBatch, DeploymentProfile, DeploymentRun, License, ManagedComputer, RepairIntervention, WorkspaceActivity, WorkspaceInvitation


@admin.register(DeploymentProfile)
class DeploymentProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "workspace", "owner", "windows_iso", "language", "updated_at")
    list_filter = ("language", "workspace")
    search_fields = ("name", "windows_iso", "owner__username", "workspace__name")


@admin.register(DeploymentBatch)
class DeploymentBatchAdmin(admin.ModelAdmin):
    list_display = ("profile", "workspace", "requested_by", "target_count", "status", "created_at")
    list_filter = ("status", "workspace", "created_at")
    readonly_fields = ("profile", "workspace", "requested_by", "target_count", "status", "created_at")


@admin.register(DeploymentRun)
class DeploymentRunAdmin(admin.ModelAdmin):
    list_display = ("batch", "machine_name", "target_disk", "status", "progress", "last_seen")
    list_filter = ("status", "created_at")
    search_fields = ("machine_name", "machine_model", "target_disk")
    readonly_fields = ("token_hash", "created_at", "expires_at", "last_seen", "finished_at")


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


@admin.register(WorkspaceActivity)
class WorkspaceActivityAdmin(admin.ModelAdmin):
    list_display = ("workspace", "actor", "action", "target_label", "created_at")
    list_filter = ("action", "workspace", "created_at")
    search_fields = ("workspace__name", "actor__username", "target_label")
    readonly_fields = ("workspace", "actor", "action", "target_label", "created_at")


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
