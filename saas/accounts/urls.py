from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    dashboard_view,
    login_view,
    logout_view,
    register_view,
    create_remediation_request,
    verify_email_view,
    create_workspace_view,
    add_workspace_member_view,
    remove_workspace_member_view,
    deployment_view,
    accept_workspace_invitation_view,
    equipment_view,
    equipment_detail_view,
    equipment_audit_report_view,
)

urlpatterns = [
    path("register/", register_view, name="register"),
    path(
        "verify-email/<uidb64>/<token>/",
        verify_email_view,
        name="verify_email",
    ),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("dashboard/deployment/", deployment_view, name="deployment"),
    path("dashboard/equipment/", equipment_view, name="equipment"),
    path("dashboard/equipment/<str:asset_tag>/", equipment_detail_view, name="equipment_detail"),
    path("dashboard/equipment/<str:asset_tag>/audit/<int:report_id>/", equipment_audit_report_view, name="equipment_audit_report"),
    path("dashboard/workspace/create/", create_workspace_view, name="create_workspace"),
    path("dashboard/workspace/members/add/", add_workspace_member_view, name="add_workspace_member"),
    path("workspace/invitation/<uuid:token>/", accept_workspace_invitation_view, name="accept_workspace_invitation"),
    path("dashboard/workspace/members/<int:member_id>/remove/", remove_workspace_member_view, name="remove_workspace_member"),
    path(
    "dashboard/remediate/<int:audit_id>/<str:category>/",
    create_remediation_request,
    name="create_remediation_request",),
]
