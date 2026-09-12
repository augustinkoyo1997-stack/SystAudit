from django.urls import path

from .views import (
    dashboard_view,
    login_view,
    logout_view,
    register_view,
    create_remediation_request,
)

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path(
    "dashboard/remediate/<int:audit_id>/<str:category>/",
    create_remediation_request,
    name="create_remediation_request",),
]